
from __future__ import print_function

import os
from setuptools import setup as _setup
from .dsocmd import DSO, Extension, build_dso, build_ext, bdist_egg

from setuptools.command.install import install

__all__ = (
    'DSO',
    'Extension',
    'build_dso',
    'build_ext',
    'bdist_egg',
    'setup',
)

def setup(**kws):
    """Wrapper around setuptools.setup() which injects extra Commands
       needed to build DSOs.
    """
    cmdclass = kws.setdefault('cmdclass', {})
    # cmdclass_setdefault sets default to cmdclass[name]=klass and verifies
    # that cmdclass[name] is a subclass of klass. This way we check, for
    # example, that build_ext overridden by user is not some arbitrary class,
    # but inherits from setuptools_dso.build_ext, which is required for
    # setuptools_dso to work correctly.
    def cmdclass_setdefault(name, klass):
        cmdclass.setdefault(name, klass)
        if not issubclass(cmdclass[name], klass):
            raise AssertionError("cmdclass[%s] must be subclass of %s" % (cmdclass[name], klass))
    cmdclass_setdefault('bdist_egg', bdist_egg)
    cmdclass_setdefault('build_dso', build_dso)
    cmdclass_setdefault('build_ext', build_ext)
    kws.setdefault('zip_safe', len(kws.get('ext_modules', []))==0 and len(kws.get('x_dsos', []))==0)
    _setup(**kws)

try:
    from Cython.Build import cythonize as _cythonize
except ImportError:
    def _cythonize(extensions, **kws):
        """dummy cythonize() used when Cython not installed.
        Assumes that generated source files are distributed.
        Cython docs say "It is strongly recommended that you
        distribute the generated .c ...".
        """
        print("Cython not installed.  Trying to use dummy cythonize()")
        for E in extensions:
            srcs = []
            for src in E.sources:
                # how to match up .pyx with .c or .cpp ?
                # there are (at least) three ways to specify language.
                # kws['language'], E.language, and as a directive in the .pyx
                # This last is not something we can detect, so try to guess.
                base, ext = os.path.splitext(src)
                if ext=='.pyx':
                    if os.path.isfile(base+'.cpp'):
                        src = base+'.cpp'
                    else:
                        src = base+'.c'
                srcs.append(src)
            E.sources[:] = srcs
        return extensions

def cythonize(orig, **kws):
    """Wrapper around Cython.Build.cythonize() to correct handling of
    DSO()s and Extension()s using them.
    """
    cmods = _cythonize(orig, **kws)
    for new, old in zip(cmods, orig):
        if new is old or not isinstance(old, Extension):
            continue
        assert isinstance(new, Extension), new
        # _cythonize() has re-created our Extension.
        # The correct class is used, but our special attributes are lost.
        # So we copy them over
        for key in ('dsos', 'lang_compile_args', 'soversion'):
            if hasattr(old, key):
                setattr(new, key, getattr(old, key))
    return cmods
