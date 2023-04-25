#!/usr/bin/env python
"""Project2 demonstrates how to link-to dsodemo and use it from external project"""

from setuptools_dso import Extension, setup
from os.path import dirname, join, abspath

import dsodemo.lib

ext = Extension('use_dsodemo.ext', ['src/use_dsodemo/ext.cpp'],
    dsos=['dsodemo.lib.demo'],
    include_dirs=[dirname(dsodemo.lib.__file__)],  # TODO automatically discover it like we do for library_dirs
)
setup(
    name='use_dsodemo',
    version="0.1",
    install_requires = ['setuptools_dso', 'dsodemo'],
    packages=['use_dsodemo'],
    package_dir={'': 'src'},
    ext_modules = [ext],
)
