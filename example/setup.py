#!/usr/bin/env python

from setuptools_dso import DSO, Extension, setup

dso = DSO('dsodemo.lib.demo', ['src/foo.c', 'src/bar.cpp'],
    define_macros = [('BUILD_FOO', None)],
    extra_compile_args = ['-DALL'],
    lang_compile_args = {
        'c':['-DISC'],
        'c++':['-DISCXX'],
    },
    soversion='1.0',
)

ext = Extension('dsodemo.ext.dtest', ['src/extension.cpp'],
    dsos=['dsodemo.lib.demo'],
)

setup(
    name='dsodemo',
    version="0.1",
    # setup/build time dependencies listed in pyproject.toml
    # cf. PEP 518
    #setup_requires = ['setuptools_dso'],
    packages=['dsodemo', 'dsodemo.ext'],
    package_dir={'': 'src'},
    ext_modules = [ext],
    x_dsos = [dso],
)
