#!/usr/bin/env python
# Copyright 2022  Michael Davidsaver
# SPDX-License-Identifier: BSD
# See LICENSE

from setuptools import setup

with open('README.md', 'r') as F:
    long_description = F.read()

setup(
    name='setuptools_dso',
    version="2.7",
    description="setuptools extension to build non-python shared libraries",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mdavidsaver/setuptools_dso',
    project_urls={
        'Documentation':'https://mdavidsaver.github.io/setuptools_dso',
        'Release Notes':'https://mdavidsaver.github.io/setuptools_dso/releasenotes.html',
    },

    author='Michael Davidsaver',
    author_email='mdavidsaver@gmail.com',
    license='BSD',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving :: Packaging',
        'Framework :: Setuptools Plugin',
        'License :: OSI Approved :: BSD License',
    ],
    python_requires='>=2.7',
    install_requires = ['setuptools'],

    packages=['setuptools_dso', 'setuptools_dso.test'],
    package_dir={'':'src'},
)
