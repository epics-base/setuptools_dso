import sys
import os
import platform
import glob

from collections import defaultdict
from importlib import import_module # say that three times fast...
from multiprocessing import Pool
import multiprocessing as MP

from setuptools import Command, Distribution, Extension as _Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.install import install
from setuptools.command.bdist_egg import bdist_egg as _bdist_egg

from distutils.sysconfig import customize_compiler
from distutils.dep_util import newer_group
from distutils.util import get_platform
from distutils import log

Distribution.x_dsos = None

if sys.version_info<(3,4) or MP.get_start_method()!='fork':
    # bypass multiprocessing optimization (parallel compile)
    # for older py (can't pickle the necessary pieces)
    # freeze_support() is a pain, and is needed by methods other than 'fork'.
    # Contrary to documentation, this is not limited to Windows.
    # https://bugs.python.org/issue32146
    # https://bugs.python.org/issue33725
    class Pool(object):
        def __init__(self, N):
            pass
        def __enter__(self):
            return self
        def __exit__(self,A,B,C):
            pass
        class DummyJob(object):
            def __init__(self, fn, args, kws):
                self._F = fn, args, kws
            def get(self):
                fn, args, kws = self._F
                return fn(*args, **kws)
        def apply_async(self, fn, args, kws):
            return self.DummyJob(fn, args, kws)

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
        mypath = os.path.join('.', *ext.name.split('.')[:-1])

        soargs = set()

        for dso in getattr(ext, 'dsos', []):
            log.debug("Will link against DSO %s"%dso)

            parts = dso.split('.')
            dsopath = os.path.join('.', *parts[:-1])
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

                    found = True
                    break

            if not found:
                raise RuntimeError("Unable to find DSO %s needed by extension %s"%(dso, ext.name))

            ext.libraries.append(parts[-1])

            if sys.platform=='win32':
                pass # nothing line -rpath available

            elif sys.platform=='darwin':
                soargs.add('-Wl,-rpath,@loader_path/%s' % os.path.relpath(dsopath, mypath))

            else:
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

        if 'NUM_JOBS' in os.environ: # because it is so very cumbersome to pass extra build args through pip and setuptools ...
            nworkers = int(os.environ['NUM_JOBS'])
        elif hasattr(os, 'cpu_count'): # py3
            nworkers = os.cpu_count()
        else:
            nworkers = 2 # why not?

        with Pool(nworkers) as P:
            jobs = []
            for lang, srcs in SRC.items():

                # submit jobs
                # allocate every n-th object to the n-th worker.
                # Load not well balanced, but easy to do.
                for inputs in [srcs[n::nworkers] for n in range(nworkers)]:
                    jobs.append(P.apply_async(self.compiler.compile, [inputs], {
                        'output_dir':self.build_temp,
                        'macros':macros,
                        'include_dirs':include_dirs,
                        'extra_postargs':extra_args + (dso.lang_compile_args.get(lang) or []),
                        'depends':dso.depends,
                    }))

            # work for completion
            [objects.extend(job.get()) for job in jobs]

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
            extra_args.extend(['-install_name', '@rpath/%s'%solibbase])

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
            build_py = self.get_finalized_command('build_py')
            pkg = '.'.join(dso.name.split('.')[:-1])    # path.to.dso -> path.to
            pkgdir = build_py.get_package_dir(pkg)      # path.to -> src/path/to

            solib_dst   = os.path.join(pkgdir, os.path.basename(solib))     # path/to/dso.so -> src/path/to/dso.so
            baselib_dst = os.path.join(pkgdir, os.path.basename(baselib))

            self.mkpath(os.path.dirname(solib_dst))
            self.copy_file(outlib, solib_dst)
            if baselib!=solib:
                self.copy_file(outbaselib, baselib_dst)

class build_ext(dso2libmixin, _build_ext):

    # allow build_ext to depend on other commands
    sub_commands = _build_ext.sub_commands[:]

    def finalize_options(self):
        _build_ext.finalize_options(self)

        self.include_dirs = massage_dir_list([self.build_temp], self.include_dirs or [])
        self.library_dirs = massage_dir_list([self.build_lib]  , self.library_dirs or [])

    def run(self):
        # original setuptools/distutils don't call sub_commands for build_ext
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

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

# _needs_builddso marks distutils/setuptools command to depend on build_dso.
#
# if right_before is specified build_dso is injected before that command
# instead of as first dependency.
def _needs_builddso(command, right_before=None):
    assert issubclass(command, Command)
    # copy to avoid changing base class if sub_commands was just inherited
    _ = command.sub_commands[:]
    where = 0
    if right_before is not None:
        for i,(name,_test) in enumerate(_):
            if name == right_before:
                where = i
                break
        else:
            raise AssertionError("command %r does not have %r subcommand" % (command, right_before))
    _.insert(where, ('build_dso', has_dsos))
    command.sub_commands = _

from distutils.command.build import build
_needs_builddso(build, right_before='build_clib')


# depend build_ext: build_dso, for DSOs to be automatically built on
# `setup.py develop` (= `pip install -e`).
#
# `setup.py develop` does not call build and instead calls `build_ext -i`
# directly without providing any kind of sub_commands support.
#
# -> so we hook into build_ext to make sure build_dso is also called.
_needs_builddso(build_ext)
