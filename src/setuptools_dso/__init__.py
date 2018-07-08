
from setuptools import setup as _setup
from .dsocmd import DSO, Extension, build_dso, build_ext

__all__ = (
    'DSO',
    'Extension',
    'build_dso',
    'build_ext',
    'setup',
)

def setup(**kws):
    cmdclass = kws.get('cmdclass', {})
    cmdclass['build_dso'] = build_dso
    cmdclass['build_ext'] = build_ext
    kws['cmdclass'] = cmdclass
    kws['zip_safe'] = kws.get('zip_safe', False) and len(kws.get('ext_modules', []))==0 and len(kws.get('x_dsos', []))==0
    _setup(**kws)
