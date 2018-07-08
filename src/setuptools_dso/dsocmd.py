import sys
import os
import platform
import glob

from collections import defaultdict
from importlib import import_module # say that three times fast...

from setuptools import Command, Distribution, Extension as _Extension
from setuptools.command.build_ext import build_ext as _build_ext

from distutils.sysconfig import customize_compiler
from distutils.dep_util import newer_group
from distutils.util import get_platform
from distutils import log

Distribution.x_dsos = None

def massage_dir_list(bdir, dirs):
    """Process a list of directories for use with -I or -L
    For relative paths, also include paths relative to a build directory
    """
    dirs = dirs or []
    dirs.extend([os.path.join(bdir, D) for D in dirs if not os.path.isabs(D)])
    return dirs

class Extension(_Extension):
    def __init__(self, name, sources,
                 dsos=None,
                 **kws):
        _Extension.__init__(self, name, sources, **kws)
        self.dsos = dsos or []

class DSO(_Extension):
    def __init__(self, name, sources,
                 soversion=None,
                 extra_compile_args=None,
                 dsos=None,
                 **kws):
        if not isinstance(extra_compile_args, dict):
            extra_compile_args = {'*':extra_compile_args}
        _Extension.__init__(self, name, sources, extra_compile_args=extra_compile_args, **kws)
        self.soversion = soversion or None
        self.dsos = dsos or []

class dso2libmixin:
    def dso2lib_pre(self, ext):
        mypath = os.path.join(*ext.name.split('.')[:-1])

        for dso in getattr(ext, 'dsos', []):
            log.debug("Will link against DSO %s"%dso)

            parts = dso.split('.')
            dsopath = os.path.join(*parts[:-1])
            if sys.platform == "win32":
                libname = parts[-1]+'.dll'
            elif sys.platform == 'darwin':
                libname = 'lib%s.dylib'%parts[-1] # find the plain version first.
            else:
                libname = 'lib%s.so'%parts[-1]

            dsosearch = [os.path.join(self.build_lib, *parts[:-1])] # maybe we just built it

            try:
                # assume this DSO lives in an external package.
                dsobase = os.path.dirname(import_module(parts[0]).__file__)
                dsodir = os.path.join(dsobase, *parts[1:-1])
                dsosearch.append(dsodir)
            except ImportError:
                pass

            found = False
            self._osx_changes = []
            for candidate in dsosearch:
                C = os.path.join(candidate, libname)
                if not os.path.isfile(C):
                    log.debug("  Not %s"%C)
                else:
                    log.debug("  Found %s"%C)
                    ext.library_dirs.append(candidate)

                    if sys.platform == 'darwin':
                        # now find the full name of the library (including major version)
                        full = glob.glob(os.path.join(candidate, 'lib%s.*.dylib'%parts[-1]))
                        if len(full)==0:
                            fullname = libname
                        elif len(full)==1:
                            fullname = os.path.basename(full[0])
                        else:
                            raise RuntimeError("Something wierd happened.  Please report. %s"%full)

                        self._osx_changes.append(('@loader_path/'+fullname, '@loader_path/%s/%s'%(os.path.relpath(dsopath, mypath), fullname)))

                        # In theory -dylib_file A:B asks the linker to do the equivlaent of:
                        #     install_name_tool -change A B
                        # But this seems not to work.  So we call install_name_tool below

                    found = True
                    break

            if not found:
                raise RuntimeError("Unable to find DSO %s needed by extension %s"%(dso, ext.name))

            ext.libraries.append(parts[-1])

            if platform.system() == 'Linux':
                ext.extra_link_args.extend(['-Wl,-rpath,$ORIGIN/%s'%os.path.relpath(dsopath, mypath)])

    def dso2lib_post(self, ext):
        if sys.platform == 'darwin':
            ext_path = self.get_ext_fullpath(ext.name)
            self.spawn(['otool', '-L', ext_path])

            for old, new in osx_changes:
                self.spawn(['install_name_tool', '-change', old, new, ext_path])

            self.spawn(['otool', '-L', ext_path])

class build_dso(dso2libmixin, Command):
    description = "Build Dynamic Shared Object (DSO).  non-python dynamic libraries (.so, .dylib, or .dll)"

    user_options = [
        ('build-lib=', 'b',
         "directory for compiled extension modules"),
        ('build-temp=', 't',
         "directory for temporary files (build by-products)"),
        ('inplace', 'i',
         "ignore build-lib and put libraries into the source " +
         "directory alongside your pure Python modules"),
        ('force', 'f',
         "forcibly build everything (ignore file timestamps)"),
    ]

    boolean_options = ['inplace', 'force']

    def initialize_options (self):
        self.dsos = None

        self.build_lib = None
        self.build_temp = None
        self.inplace = None
        self.force = None

    def finalize_options(self):
        from distutils import sysconfig

        self.set_undefined_options('build_ext',
                                   ('build_lib', 'build_lib'),
                                   ('build_temp', 'build_temp'),
                                   ('inplace', 'inplace'),
                                   ('force', 'force'),
                                   )

        self.dsos = self.distribution.x_dsos

    def run(self):
        if self.dsos is None:
            log.debug("No DSOs to build")
            return

        log.info("Building DSOs")
        from distutils.ccompiler import new_compiler

        self.compiler = new_compiler(#compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        customize_compiler(self.compiler)

        # fixup for MAC to build dylib (MH_DYLIB) instead of bundle (MH_BUNDLE)
        if sys.platform == 'darwin':
            for i,val in enumerate(self.compiler.linker_so):
                if val=='-bundle':
                    self.compiler.linker_so[i] = '-dynamiclib'

        for dso in self.dsos:
            self.dso2lib_pre(dso)
            self.build_dso(dso)
            self.dso2lib_post(dso)

    def _name2file(self, dso, so=False):
        parts = dso.name.split('.')

        if sys.platform == "win32":
            parts[-1] = parts[-1]+'.dll'

        elif sys.platform == 'darwin':
            if so and dso.soversion is not None:
                parts[-1] = 'lib%s.%s.dylib'%(parts[-1], dso.soversion)
            else:
                parts[-1] = 'lib%s.dylib'%(parts[-1],)

        else: # ELF
            if so and dso.soversion is not None:
                parts[-1] = 'lib%s.so.%s'%(parts[-1], dso.soversion)
            else:
                parts[-1] = 'lib%s.so'%(parts[-1],)

        return os.path.join(*parts)


    def build_dso(self, dso):
        baselib = self._name2file(dso)
        solib = self._name2file(dso, so=True)

        outbaselib = os.path.join(self.build_lib, baselib)
        outlib = os.path.join(self.build_lib, solib)
        sources = list(dso.sources)

        depends = sources + dso.depends
        if not (self.force or newer_group(depends, outlib, 'newer')):
            log.debug("skipping '%s' DSO (up-to-date)", dso.name)
            return
        else:
            log.info("building '%s' DSO as %s", dso.name, outlib)

        macros = dso.define_macros[:]
        for undef in dso.undef_macros:
            macros.append((undef,))

        extra_args = dso.extra_compile_args.get('*', []) or []

        include_dirs = massage_dir_list(self.build_temp, dso.include_dirs or [])

        SRC = defaultdict(list)

        # sort by language
        for src in sources:
            SRC[self.compiler.language_map[os.path.splitext(src)[-1]]].append(src)

        # do the actual compiling
        objects = []
        for lang, srcs in SRC.items():
            objects.extend(self.compiler.compile(srcs,
                                            output_dir=self.build_temp,
                                            macros=macros,
                                            include_dirs=include_dirs,
                                            #debug=self.debug,
                                            extra_postargs=dso.extra_compile_args.get('*', []) + dso.extra_compile_args.get(lang, []),
                                            depends=dso.depends))

        library_dirs = massage_dir_list(self.build_lib, dso.library_dirs or [])

        # the Darwin linker errors if given non-existant -L directories :(
        [self.mkpath(D) for D in library_dirs]

        if dso.extra_objects:
            objects.extend(dso.extra_objects)

        extra_args = []

        if sys.platform == 'darwin':
            # we always want to produce relocatable (movable) binaries
            # TODO: this only works when library and extension are in the same directory
            extra_args.extend(['-install_name', '@loader_path/%s'%os.path.basename(solib)])
        elif sys.platform != "win32" and baselib!=solib:
            extra_args.extend(['-Wl,-h,%s'%os.path.basename(solib)])

        if sys.platform == "win32":
            # The .lib is considered "temporary" for extensions, but not for us
            # so we pass export_symbols=None and put it along side the .dll
            extra_args.append('/IMPLIB:%s.lib'%(os.path.splitext(outlib)[0]))

        extra_args.extend(dso.extra_link_args or [])

        language = dso.language or self.compiler.detect_language(sources)

        self.compiler.link_shared_object(
            objects, outlib,
            libraries=dso.libraries,
            library_dirs=library_dirs,
            runtime_library_dirs=dso.runtime_library_dirs,
            extra_postargs=extra_args,
            export_symbols=None,
            #debug=self.debug,
            build_temp=self.build_temp,
            target_lang=language)

        if baselib!=solib:
            self.copy_file(outlib, outbaselib) # link="sym" seem to get the target path wrong

        if self.inplace:
            self.copy_file(outlib, solib)
            if baselib!=solib:
                self.copy_file(outbaselib, baselib)

class build_ext(dso2libmixin, _build_ext):
    def finalize_options(self):
        _build_ext.finalize_options(self)

        # MSVC build puts .lib in build/temp.*
        # others put .so in build/lib.*
        #self.lib_temp = self.build_temp if sys.platform == "win32" else self.build_lib

        self.include_dirs = massage_dir_list(self.build_temp, self.include_dirs or [])
        self.library_dirs = massage_dir_list(self.build_lib  , self.library_dirs or [])

    def run(self):
        self.run_command('build_dso')
        # the Darwin linker errors if given non-existant directories :(
        [self.mkpath(D) for D in self.library_dirs]
        _build_ext.run(self)

    def build_extension(self, ext):
        ext.include_dirs = massage_dir_list(self.build_temp, ext.include_dirs or [])
        ext.library_dirs = massage_dir_list(self.build_lib  , ext.library_dirs or [])

        ext.extra_link_args = ext.extra_link_args or []

        self.dso2lib_pre(ext)

        # the Darwin linker errors if given non-existant directories :(
        [self.mkpath(D) for D in ext.library_dirs]

        _build_ext.build_extension(self, ext)

        self.dso2lib_post(ext)
