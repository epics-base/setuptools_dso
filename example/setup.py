#!/usr/bin/env python

from setuptools_dso import DSO, Extension, setup
from setuptools_dso.probe import ProbeToolchain

def define_DSOs(cmd):
    # 'cmd' is instance of distutils Command with attributes:
    # 'build_lib', 'build_temp', 'inplace', 'distribution', etc.

    # example of inspecting the target toolchain.
    # could be used to alter source list, macro definitions, or compiler flags.
    probe = ProbeToolchain()
    assert probe.try_compile('#include <stdlib.h>')
    assert not probe.try_compile('intentionally invalid syntax')
    assert probe.check_include('stdlib.h')
    assert not probe.check_include('no-such-header.h')
    assert probe.sizeof('short')==2
    assert probe.check_symbol('RAND_MAX', headers=['stdlib.h'])
    assert probe.check_symbol('abort', headers=['stdlib.h'])
    assert not probe.check_symbol('intentionally_undeclared_symbol', headers=['stdlib.h'])

    dso = DSO('dsodemo.lib.demo', ['src/foo.c', 'src/bar.cpp'],
        define_macros = [('BUILD_FOO', None)],
        # demonstrate passing other compiler flags, either conditionally or not.
        # these are not actually used.
        extra_compile_args = ['-DALL'],
        lang_compile_args = {
            'c':['-DISC'],
            'c++':['-DISCXX'],
        },
        # demonstrate how to set an SONAME.
        # eg. on linux the result will be two files:
        #   dsodemo/lib/libdemo.so
        #   dsodemo/lib/libdemo.so.1.0
        soversion='1.0',
    )

    return [dso]

ext = Extension('dsodemo.ext.dtest', ['src/extension.cpp'],
    dsos=['dsodemo.lib.demo'],
)

setup(
    name='dsodemo',
    version="0.1",
    # setup/build time dependencies listed in pyproject.toml
    # cf. PEP 518
    #setup_requires = ['setuptools_dso'],
    # also need at runtime for DSO filename lookup since demo uses ctypes
    install_requires = ['setuptools_dso'],
    packages=['dsodemo', 'dsodemo.ext', 'dsodemo.lib'],
    package_dir={'': 'src'},
    ext_modules = [ext],
    # 'x_dsos' may be None, a list of DSO instances,
    # or a callable returning a list of DSOs.
    #x_dsos = [dso],
    x_dsos = define_DSOs,
)
