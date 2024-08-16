.. _probing:

Probing Toolchain
=================

.. currentmodule:: setuptools_dso

Replacing buildsystems like autoconf or cmake may require compile time
inspection of the toolchain to determine sizes of types, the availability
of header files, or similar.
The `ProbeToolchain` class exists to allow these questions to be answered. ::

    from setuptools_dso import DSO, ProbeToolchain

    def define_DSOS(cmd):
        mymacros = []
        probe = ProbeToolchain()

        if probe.check_include('linux/sonet.h'):
            mymacros += [('ENABLE_OBSCURE_FEATURE', None)]

        return [DSO('dsodemo.lib.demo',
            ['src/foo.c', 'src/bar.cpp'],
            define_macros = mymacros,
            ...)]

    setup(
        ...
        x_dsos = define_DSOS, # lazy DSOs list to avoid redundant probing
        zip_safe = False,
    )

.. _probe_classify:

Toolchain Classification
------------------------

:py:attr:`ProbeToolchain.info` is a :py:class:`probe.ToolchainInfo` object based
on compiler specific predefined preprocessor macros. ::

    from setuptools_dso import ProbeToolchain

    probe = ProbeToolchain()
    if probe.info.compiler=='gcc' and probe.info.compiler_version<(4,9,4):
        print("GCC version is too old")

.. autoclass:: ProbeToolchain
    :members:

.. autoclass:: setuptools_dso.probe.ToolchainInfo
    :members:
