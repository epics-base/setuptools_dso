# setuptools extension for building non-Python Dynamic Shared Objects

Building non-python shared libraries (eg. `libY.so`, `libY.dylib`, or `Y.dll`) for inclusion in a Python Wheel.

This extension provides at alternative to bundling externally built
libraries in Python Wheel packages.  This replaces an external
build system (eg. Makefile), allowing non-python libraries to be
built from source within the python ecosystem.

See [example/setup.py](example/setup.py) for a working example.

[![setuptools-dso](https://github.com/mdavidsaver/setuptools_dso/workflows/setuptools-dso/badge.svg)](https://github.com/mdavidsaver/setuptools_dso/actions)

## Building packages

Packages using `setuptools_dso` can for the most part be treated like any other python package.
Distribution through [pypi.org](https://pypi.org/) as source and/or binary (wheels) is possible.
Like other packages containing compiled code, use of egg binaries is not supported.

Use of PIP is encouraged.
The `setuptools_dso` package needs to be installed when manually invoking `setup.py` scripts in dependent packages.
eg. to generate source tars with `setup.py sdist`.

Developers wishing to work with an in-place build will need to use the added `build_dso` command,
which functions like the `build_ext` command.

```sh
python setup.py build_dso -i
python setup.py build_ext -i
```

## Usage

The [example/](example/) demonstrates building a non-python library,
and linking it with a python extension module.

### pyproject.toml

To properly support `pip install ...`, it is recommended to include a
[`pyproject.toml`](https://www.python.org/dev/peps/pep-0518/)
file containing at least:

```
[build-system]
requires = ["setuptools", "wheel", "setuptools_dso"]
```

This ensures that `setuptools_dso` is available to be imported by `setup.py`.

### MANIFEST.in

Add a `MANIFEST.in` to ensure that `setup.py sdist` includes everything necessary
for a successful source build.

```
include pyproject.toml
include src/*.h
include src/*.c
include src/*.cpp
```

### Building a DSO

The [source](example/src/) files while make up the non-python `demo` library are: `mylib.h`, `foo.c`, `bar.cpp`.
This library will be expressed as a `setuptools_dso.DSO` object.
The first argument is a directory path and library base name encoded like a python module.
eg. the result of `dsodemo.lib.demo` will be eg. `dsodemo/lib/libdemo.so` or `dsodemo\lib\demo.dll`
installed in the python module tree along-side any other python code or C extensions.

Note that there need not be a `dsodemo/lib/__init__.py` as `dsodemo.lib` need not be a python package.

```py
from setuptools_dso import DSO, Extension, setup

dso = DSO('dsodemo.lib.demo', ['src/foo.c', 'src/bar.cpp'], ...)

setup(
    ...
    x_dsos = [dso],
    zip_safe = False, # setuptools_dso is not compatible with eggs!
)
```

The `DSO` constructor understands all of the same keyword arguments as `setuptools.Extension`
and [`distutils.core.Extension`](https://docs.python.org/3/distutils/apiref.html#distutils.core.Extension),
with the addition of `dsos=[...]`, `soversion='...'`, and `lang_compile_args={'...':'...'}`.

The `dsos=` argument is a list of other `DSO` names (eg. `'dsodemo.lib.demo'`) to allow
one `DSO` to be linked against others.

eg. `dsos=['some.lib.foo']` will result in something like `gcc ... -L.../some/lib -lfoo`.

### Building an Extension

`setuptools_dso.Extension` is a wrapper around `setuptools.Extension` which adds the `dsos=[...]` keyword argument.
This allows a C extension module to be linked against a `DSO` by name.
The named `DSO` may be built by the same `setup.py`, or may already be present in `$PYTHONPATH`.

```py
from setuptools_dso import DSO, Extension, setup

ext = Extension('dsodemo.ext.dtest', ['src/extension.cpp'],
    dsos=['dsodemo.lib.demo'],
)

setup(
    ...
    ext_modules = [ext],
    zip_safe = False, # setuptools_dso is not compatible with eggs!
)
```

### Runtime

Some additional runtime preparation is need to in order to find the `'dsodemo.lib.demo'` library
when the `dsodemo.ext.dtest` Extension is imported on Windows.
The example places this in [`example/src/dsodemo/__init__.py`](example/src/dsodemo/__init__.py)
to ensure it always runs before the extension library is loaded.

```py
import sys, os

def fixpath():
    path = os.environ.get('PATH', '').split(os.pathsep)
    libdir = os.path.join(os.path.dirname(__file__), 'lib')
    path.append(libdir)
    os.environ['PATH'] = os.pathsep.join(path)

    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(libdir)

if sys.platform == "win32":
    fixpath()
```

## Mechanics

Libraries build with setuptools-dso will typically be linked, directly or indirectly, to python extension modules.
Such libraries should loaded implicitly when the extension module is imported by the python runtime.
For this to work the OS runtime loader must be able to find these libraries.
This is complicated by OS differences, and a desire to support virtualenv and similar.

Supporting virtualenv prevents the use of absolute build time paths.

The resolutions to this complication differ for each OS depending on the
capabilities of the executable format used.

### ELF (Linux, *NIX, *BSD)

For ELF (Executable and Linking Format) targets the RPATH mechanism is used with the magic $ORIGIN/ prefix.

Take as an example the following installed module tree:

```
* modulea
 * __init__.py
 * _ext.so
 * lib
  * libsup.so
  * libsup.so.0
```

The supporting library is then linked with a library name of `libsup.so.0`
(eg. `gcc -o libsup.so.0 -shared -Wl,-soname,libsup.so.0 ...`)

When linking a dependent library or extension module `-Wl,-rpath,'$ORIGIN/lib'`
is given since the relative path from `_ext.so` to `libsup.so.0` is `./lib`.

Note that on Linux runtime linking is really a function of the libc (eg. glibc).

### Mach-O (OSX)

Historically Mach-O did not support anything like RPATH.
However, it now does (cf. 'man dyld')

The equivalence with GCC+ELF is for `-Wl,-soname,libsup.so.0` to become `-install\_name @rpath/libsup.0.dylib`.
Then `-Wl,-rpath,'$ORIGIN/lib'` becomes `-Wl,-rpath,@loader_path/lib`.

### PE (Windows)

There is no equivalent for RPATH.
It is necessary to adjust the loader search path to include the directory
containing the support library dll explicitly from python code prior to loading the extension.
(eg. from an `__init__.py`)

With earlier versions of Windows it is sufficient to adjust `%PATH%`.
Recent versions require use of the `AddDllDirectory()` API call.
Python wraps this as `os.add_dll_directory()`.
