setuptools extension for building non-Python Dynamic Shared Objects
===================================================================

.. module:: setuptools_dso


Building non-python shared libraries (eg. `libY.so`, `libY.dylib`, or `Y.dll`) for inclusion in a Python Wheel.

This `setuptools <https://pypi.org/project/setuptools/>`_ extension
provides at alternative to bundling externally built libraries in Python Wheel packages.
This replaces an external build system (eg. Makefile),
allowing non-python libraries to be built from source within a python ecosystem.

- `Issue tracker <https://github.com/mdavidsaver/setuptools_dso/issues>`_
- On `PYPI <https://pypi.org/project/setuptools-dso/>`_
- `VCS repository <https://github.com/mdavidsaver/setuptools_dso>`_
- Canonical `documentation <https://mdavidsaver.github.io/setuptools_dso>`_
- `Example usage <https://github.com/mdavidsaver/setuptools_dso/tree/master/example>`_
- CI status |cistatus|

.. |cistatus| image:: https://github.com/mdavidsaver/setuptools_dso/workflows/setuptools-dso/badge.svg
    :target: https://github.com/mdavidsaver/setuptools_dso/actions
    :alt: github actions status badge

.. toctree::
   :maxdepth: 2

   usage
   details
