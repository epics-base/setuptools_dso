#!/usr/bin/env python

from setuptools import Extension
from setuptools_dso import DSO, build_dso, build_ext, setup

dso = DSO('dsodemo.demo', ['foo.c', 'bar.cpp'],
    define_macros = [('BUILD_FOO', None)],
    extra_compile_args = {
        '*':['-DALL'],
        'c':['-DISC'],
        'c++':['-DISCXX'],
    },
    soversion='1.0',
)

ext = Extension('dsodemo.dtest', ['extension.cpp'],
    library_dirs=['dsodemo'],
    libraries=['demo'],
)

setup(
    name='dsodemo',
    version="0.1",
    packages=['dsodemo'],
    ext_modules = [ext],
    x_dsos = [dso],
)
