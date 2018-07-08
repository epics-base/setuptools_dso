#!/usr/bin/env python

from setuptools_dso import DSO, Extension, build_dso, build_ext, setup

dso = DSO('dsodemo.lib.demo', ['foo.c', 'bar.cpp'],
    define_macros = [('BUILD_FOO', None)],
    extra_compile_args = {
        '*':['-DALL'],
        'c':['-DISC'],
        'c++':['-DISCXX'],
    },
    soversion='1.0',
)

ext = Extension('dsodemo.ext.dtest', ['extension.cpp'],
    dsos=['dsodemo.lib.demo'],
)

setup(
    name='dsodemo',
    version="0.1",
    packages=['dsodemo', 'dsodemo.ext'],
    ext_modules = [ext],
    x_dsos = [dso],
)
