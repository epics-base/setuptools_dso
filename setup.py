#!/usr/bin/env python

from setuptools import setup, Extension

with open('README.md', 'r') as F:
    long_description = F.read()

setup(
    name='setuptools_dso',
    version="2.3",
    description="setuptools extension to build non-python shared libraries",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/mdavidsaver/setuptools_dso',
    project_urls={
        'Documentation':'https://mdavidsaver.github.io/setuptools_dso',
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

    packages=['setuptools_dso'],
    package_dir={'':'src'},
)
