Probing Toolchain
=================

.. currentmodule:: setuptools_dso

Replacing buildsystems like autoconf or cmake may require compile time
inspection of the toolchain to determine sizes of types, the availability
of header files, or similar.
The `ProbeToolchain` class exists to allow these questions to be answered.

.. autoclass:: ProbeToolchain
    :members:
