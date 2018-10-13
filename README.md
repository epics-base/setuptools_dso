setuptools extension for building non-Python Dynamic Shared Objects
===================================================================

Building non-python shared libraries (eg. libY.so or Y.dll) for inclusion in a Python Wheel.

This extension provides at alternative to bundling externally built
libraries in Python Wheel packages.  This is to replace the external
build system (eg. Makefile).

If you have to ask "why", then keep moving along.  There is nothing for you to see here.

See [example/setup.py](example/setup.py) for usage.
