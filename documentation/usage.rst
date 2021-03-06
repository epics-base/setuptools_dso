
Working with packages using setuptools_dso
==========================================

.. currentmodule:: setuptools_dso

Packages using `setuptools_dso` can for the most part be treated like any other python package.
Distribution through `pypi.org <https://pypi.org/>`_ as source and/or binary (wheels) is possible.
Like other packages containing compiled code, use of egg binaries is not supported.

Use of PIP is encouraged.
The :py:mod:`setuptools_dso` package needs to be installed when manually invoking ``setup.py`` scripts in dependent packages.
eg. to generate source tars with ``setup.py sdist``.

Developers wishing to work with an in-place build will need to use the added ``build_dso`` command,
which functions like the ``build_ext`` command. ::

    python setup.py build_dso -i
    python setup.py build_ext -i

Usage
-----

The `example/ <https://github.com/mdavidsaver/setuptools_dso/tree/master/example>`_ demonstrates building a non-python library,
and linking it with a python extension module.

pyproject.toml
^^^^^^^^^^^^^^

To properly support ``pip install ...``, it is recommended to include a
`pyproject.toml <https://www.python.org/dev/peps/pep-0518/>`_
file containing at least: ::

    [build-system]
    requires = ["setuptools", "wheel", "setuptools_dso"]

This ensures that ``setuptools_dso`` is available to be imported by ``setup.py``.

MANIFEST.in
^^^^^^^^^^^

Add a ``MANIFEST.in`` to ensure that ``setup.py sdist`` includes everything necessary
for a successful source build. ::

    include pyproject.toml
    include src/*.h
    include src/*.c
    include src/*.cpp

Building a DSO
^^^^^^^^^^^^^^

.. autofunction:: setup

.. autoclass:: DSO

The `example source <https://github.com/mdavidsaver/setuptools_dso/tree/master/example/src>`_
files while make up the non-python ``demo`` library are: ``mylib.h``, ``foo.c``, ``bar.cpp``.
This library will be expressed as a `setuptools_dso.DSO` object.
The first argument is a directory path and library base name encoded like a python module.
eg. the result of ``dsodemo.lib.demo`` will be eg. ``dsodemo/lib/libdemo.so`` or ``dsodemo\lib\demo.dll``
installed in the python module tree along-side any other python code or C extensions.

Note that there need not be a ``dsodemo/lib/__init__.py`` as ``dsodemo.lib`` need not be a python package.
However, if this file is present, then the generated `dsodemo/lib/demo_dsoinfo.py` will be accessible. ::

    from setuptools_dso import DSO, Extension, setup

    dso = DSO('dsodemo.lib.demo', ['src/foo.c', 'src/bar.cpp'], ...)

    setup(
        ...
        x_dsos = [dso],
        zip_safe = False, # setuptools_dso is not compatible with eggs!
    )

The :py:class:`DSO` constructor understands the same keyword arguments as `setuptools.Extension`
and `distutils.core.Extension <https://docs.python.org/3/distutils/apiref.html#distutils.core.Extension>`_,
with the addition of ``dsos=[...]``, ``soversion='...'``, and ``lang_compile_args={'...':'...'}``.

The ``dsos=`` argument is a list of other :py:class:`DSO` names (eg. ``'dsodemo.lib.demo'``) to allow
one :py:class:`DSO` to be linked against others.

eg. ``dsos=['some.lib.foo']`` will result in something like ``gcc ... -L.../some/lib -lfoo``.

Building an Extension
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: Extension

:py:class:`setuptools_dso.Extension` is a wrapper around ``setuptools.Extension`` which adds the ``dsos=[...]`` keyword argument.
This allows a C extension module to be linked against a ``DSO`` by name.
The named ``DSO`` may be built by the same ``setup.py``, or may already be present in ``$PYTHONPATH``. ::

    from setuptools_dso import DSO, Extension, setup

    ext = Extension('dsodemo.ext.dtest', ['src/extension.cpp'],
        dsos=['dsodemo.lib.demo'],
    )

    setup(
        ...
        ext_modules = [ext],
        zip_safe = False, # setuptools_dso is not compatible with eggs!
    )

Cython
^^^^^^

.. autofunction:: cythonize

Version 1.3 added a :py:func:`setuptools_dso.cythonize()` wrapper to correctly handle ``Extension(dso=...)``.

Runtime
-------

Beginning with setuptools-dso 2.0 a file ``*_dsoinfo.py`` will be generated alongside each DSO.
eg. dso ``"mypkg.lib.thelib"`` will create ``mypkg/lib/thelib_dsoinfo.py``.
If ``mypkg.lib`` is a valid python packages (contains ``__init__.py``)
then :py:func:`setuptools_dso.runtime.import_dsoinfo` may be used to retrieve
build time information about the DSO including platform specific filename
(eg. ``thelib.dll`` vs. ``libthelib.so``).

Beginning with 2.0 the necessary additions to ``$PATH`` or calls to ``os.add_dll_directory()``
can be made via `:py:func:`dylink_prepare_dso`.

.. autofunction:: dylink_prepare_dso

Prior to 2.0, or if the generated module is not used,
some additional runtime preparation is needed in order to find the ``"dsodemo.lib.demo"`` library
when the ``dsodemo.ext.dtest`` Extension is imported on Windows.
This could be placed in eg. ``example/src/dsodemo/__init__.py``
to ensure it always runs before the extension library is loaded. ::

    # with setuptools_dso >= 2.0a1
    #from setuptools_dso import dylink_prepare_dso
    #dylink_prepare_dso('..lib.demo')

    # or as previously:

    import sys, os

    def fixpath():
        # If this file is
        #   .../ext/__init__.py
        # DSOs are under
        #   .../lib/
        libdir = os.path.join(os.path.dirname(os.path.dirname(__file__)))

        if hasattr(os, 'add_dll_directory'): # py >= 3.8
            os.add_dll_directory(libdir)
        else:
            path = os.environ.get('PATH', '').split(os.pathsep)
            path.append(libdir)
            os.environ['PATH'] = os.pathsep.join(path)

    if sys.platform == "win32":
        fixpath()

Use with ctypes
^^^^^^^^^^^^^^^

.. autofunction:: find_dso

Info
^^^^

.. autofunction:: setuptools_dso.runtime.import_dsoinfo
