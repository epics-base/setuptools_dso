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

.. autoclass:: ProbeToolchain
    :members:
