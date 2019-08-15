import sys
import os
import platform
import glob

from collections import defaultdict
from importlib import import_module # say that three times fast...

from setuptools import Command, Distribution, Extension as _Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.install import install
from setuptools.command.bdist_egg import bdist_egg as _bdist_egg
from distutils.command.build import build

from distutils.sysconfig import customize_compiler
from distutils.dep_util import newer_group
from distutils.util import get_platform
from distutils import log

Distribution.x_dsos = None

def massage_dir_list(bdirs, indirs):
    """Process a list of directories for use with -I or -L
    For relative paths, also include paths relative to a build directory
    """
    indirs = indirs or []
    dirs = indirs[:]

    for bdir in bdirs:
        dirs.extend([os.path.join(bdir, D) for D in indirs if not os.path.isabs(D)])
        if os.name == 'nt':
            bdir = os.path.dirname(bdir) # strip /Release or /Debug
            dirs.extend([os.path.join(bdir, D) for D in indirs if not os.path.isabs(D)])

    return list(filter(os.path.isdir, dirs))

def expand_sources(cmd, sources):
    for i,src in enumerate(sources):
        if os.path.exists(src):
            continue
        cand = os.path.join(cmd.build_temp, src)
        if os.path.exists(cand):
            sources[i] = cand
            continue
        if os.name == 'nt':
            cand = os.path.join(os.path.dirname(cmd.build_temp), src) # strip /Release or /Debug
            if os.path.exists(cand):
                sources[i] = cand
                continue
        raise RuntimeError("Missing source file: %s"%src)

class Extension(_Extension):
    def __init__(self, name, sources,
                 dsos=None,
                 **kws):
        _Extension.__init__(self, name, sources, **kws)
        self.dsos = dsos or []

class DSO(_Extension):
    def __init__(self, name, sources,
                 soversion=None,
                 lang_compile_args=None,
                 dsos=None,
                 **kws):
        _Extension.__init__(self, name, sources, **kws)
        self.lang_compile_args = lang_compile_args or {}
        self.soversion = soversion or None
        self.dsos = dsos or []

class dso2libmixin:
    def dso2lib_pre(self, ext):
        mypath = os.path.join(*ext.name.split('.')[:-1])

        soargs = set()
        self._osx_changes = []

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

                        # In theory '-dylib_file A:B' asks the linker to do the equivlaent of:
                        #     install_name_tool -change A B
                        # But this seems not to work.  So we call install_name_tool below

                    found = True
                    break

            if not found:
                raise RuntimeError("Unable to find DSO %s needed by extension %s"%(dso, ext.name))

            ext.libraries.append(parts[-1])

            if sys.platform not in ('darwin', "win32"):
                # Some versions of GCC will expand shell macros _internally_ when
                # passing arguments to 'ld', and need '\$ORIGIN'.  And some versions don't,
                # and fail with '\$ORIGIN'.
                # Presumably this was a bug in gcc-wrapper which was fixed at some point.
                #
                # So what to do?
                # For lack of a better idea, give both versions and hope that the non-functional
                # one is really non-functional.
                soargs.add('-Wl,-rpath,$ORIGIN/%s'%os.path.relpath(dsopath, mypath))
                soargs.add(r'-Wl,-rpath,\$ORIGIN/%s'%os.path.relpath(dsopath, mypath))

        ext.extra_link_args.extend(list(soargs))

    def dso2lib_post(self, ext_path):
        if sys.platform == 'darwin':
            self.spawn(['otool', '-L', ext_path])

            for old, new in self._osx_changes:
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

    # eg. allow injection of extra work (eg. code generation)
    # before DSOs are built
    sub_commands = []

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
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

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
            self.build_dso(dso)

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
        self.dso2lib_pre(dso)
        expand_sources(self, dso.sources)
        expand_sources(self, dso.depends)

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

        extra_args = dso.extra_compile_args or []

        include_dirs = massage_dir_list([self.build_temp, self.build_lib], dso.include_dirs or [])

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
                                            extra_postargs=extra_args + (dso.lang_compile_args.get(lang) or []),
                                            depends=dso.depends))

        library_dirs = massage_dir_list([self.build_lib], dso.library_dirs or [])

        # the Darwin linker errors if given non-existant -L directories :(
        [self.mkpath(D) for D in library_dirs]

        if dso.extra_objects:
            objects.extend(dso.extra_objects)

        extra_args = dso.extra_link_args or []
        solibbase = os.path.basename(solib)

        if sys.platform == 'darwin':
            # we always want to produce relocatable (movable) binaries
            # this install_name will be replaced below (cf. 'install_name_tool')
            extra_args.extend(['-install_name', '@loader_path/%s'%solibbase])

        elif sys.platform == "win32":
            # The .lib is considered "temporary" for extensions, but not for us
            # so we pass export_symbols=None and put it along side the .dll
            extra_args.append('/IMPLIB:%s.lib'%(os.path.splitext(outlib)[0]))

        elif baselib!=solib: # ELF
            extra_args.extend(['-Wl,-h,%s'%solibbase])

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

        self.dso2lib_post(outlib)

        if baselib!=solib:
            # we make best effort here, even though zipfiles (.whl or .egg) will contain copies
            log.info("symlink %s <- %s", solibbase, outbaselib)
            if not self.dry_run:
                if os.path.exists(outbaselib):
                    os.unlink(outbaselib)
                os.symlink(solibbase, outbaselib)
            #self.copy_file(outlib, outbaselib) # link="sym" seem to get the target path wrong

        if self.inplace:
            self.mkpath(os.path.dirname(solib))
            self.copy_file(outlib, solib)
            if baselib!=solib:
                self.copy_file(outbaselib, baselib)

class build_ext(dso2libmixin, _build_ext):
    def finalize_options(self):
        _build_ext.finalize_options(self)

        self.include_dirs = massage_dir_list([self.build_temp], self.include_dirs or [])
        self.library_dirs = massage_dir_list([self.build_lib]  , self.library_dirs or [])

    def run(self):
        # the Darwin linker errors if given non-existant directories :(
        [self.mkpath(D) for D in self.library_dirs]
        _build_ext.run(self)

    def build_extension(self, ext):
        expand_sources(self, ext.sources)
        expand_sources(self, ext.depends)

        ext.include_dirs = massage_dir_list([self.build_temp], ext.include_dirs or [])
        ext.library_dirs = massage_dir_list([self.build_lib]  , ext.library_dirs or [])

        ext.extra_link_args = ext.extra_link_args or []

        self.dso2lib_pre(ext)

        # the Darwin linker errors if given non-existant directories :(
        [self.mkpath(D) for D in ext.library_dirs]

        _build_ext.build_extension(self, ext)

        self.dso2lib_post(self.get_ext_fullpath(ext.name))

# Rant:
#   Arranging for 'build_dso' to be run is seriously annoying!
#
#   distutils presents such a simple idea.  We just add 'build_dso' to build.sub_commands.
#   'install' will first run 'build', and we're done for everything except 'bdist_egg'.
#
#   Enter setuptools...  setuptools decides to automagically alias 'install' as 'bdist_egg'.
#   Seriously 'magic', it's inspecting the strack frames...
#
#   'bdist_egg' is a special little snowflake (aka. total hack) which doesn't run 'build'
#   or 'install' (fuck!), but does it's own thing by piecemeal calling
#   eg. 'egg_info', 'build_clib' (conditionally), 'install_lib'.
#
# so what to do...
#
# 1. insert 'build_dso' before 'build_clib' in the 'build' sequence.
#    This handles everything except 'bdist_egg' (aka. 'setup.py install')...
#
# 2. override 'bdist_egg' to run 'build_dso' at an appropriate point.

def has_dsos(cmd):
    return len(getattr(cmd.distribution, 'x_dsos', None) or [])>0

class bdist_egg(_bdist_egg):
    # An ugly hack on top of an ugly hack...
    #
    # we can't hook into 'egg_info' unconditionally, as other targets like 'sdist'
    # don't want to build things...
    # so instead we hook in and run 'build_dso' just after 'egg_info'.
    def run_command(self, cmd):
        _bdist_egg.run_command(self, cmd)
        if cmd=='egg_info' and has_dsos(self):
            self.run_command('build_dso')

for i,(name,_test) in enumerate(build.sub_commands):
    if name=='build_clib':
        build.sub_commands.insert(i, ('build_dso', has_dsos))
        break
