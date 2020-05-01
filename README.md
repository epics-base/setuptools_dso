# setuptools extension for building non-Python Dynamic Shared Objects

Building non-python shared libraries (eg. libY.so or Y.dll) for inclusion in a Python Wheel.

This extension provides at alternative to bundling externally built
libraries in Python Wheel packages.  This replaces an external
build system (eg. Makefile).

See [example/setup.py](example/setup.py) for usage.


## Use case and mechanics

Libraries build with setuptools-dso will typically be linked, directly or indirectly, to python extension modules.
Such libraries should loaded implicitly when the extension module is imported by the python runtime.
For this to work the OS runtime loader must be able to find these libraries.
This is complicated by OS differences, and a desire to support virtualenv and similar.

Supporting virtualenv prevents the use of absolute build time paths.

The resolutions to this complication differ for each OS depending on the
capabilities of the executable format used.

### ELF (Linux, *NIX, *BSD)

For ELF (Executable and Linking Format) targets the RPATH mechanism is used with the magic $ORIGIN/ prefix.

Note that on Linux runtime linking is really a function of the libc (aka glibc).

Imagine a directory tree:

* modulea
 * __init__.py
 * _ext.so
 * lib
  * libsup.so
  * libsup.so.0

The supporting library is then linked with a library name of "libsup.so.0"
(eg. "gcc -o libsup.so.0 -shared -Wl,-soname,libsup.so.0 ...")

When linking a dependent library or extension module "-Wl,-rpath,'$ORIGIN/lib'"
is given since the relative path from _ext.so to libsup.so.0 is './lib'.

### Mach-O (OSX)

Historically Mach-O did not support anything like RPATH.
However, it now does (cf. 'man dyld')

The equivalence with GCC+ELF is for "-Wl,-soname,libsup.so.0" to become "-install\_name @rpath/libsup.0.dylib".
Then "-Wl,-rpath,'$ORIGIN/lib'" becomes "-Wl,-rpath,@loader_path/lib".

### PE (Windows)

There is no equivalent for RPATH.
It is necessary to adjust the loader search path to include the directory
containing the support library dll explicitly from python code prior to loading the extension.
(eg. from an \_\_init\_\_.py)

With older versions of Windows it is sufficient to adjust %PATH%.
Newer versions require use of the `AddDllDirectory()` API call.
Python wraps this as `os.add_dll_directory()`.
