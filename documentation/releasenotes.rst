.. _releasenotes:

Release Notes
=============

.. currentmodule:: setuptools_dso

2.10 (Nov 2023)
---------------

* Support for namespace packages (Nathan Shiraini)
* Propagate inplace to all sub-Command (Nathan Shiraini)
* correctly test for aarch64 endianness

2.9 (June 2023)
---------------

* Extend and fixup :py:meth:`ProbeToolchain.eval_macros`.  Adds ``language=`` argument, and fix when headers are included.

2.8 (May 2023)
--------------

* Fix linking to editable install on Windows  (Kirill Smelkov)
* Try to limit parallel compile default by RAM as well as CPU.  On Linux only.
* Document :ref:`num_jobs`, understood since 1.4.

2.7 (Feb 2023)
--------------

* Ensure package with DSO but no Extension is installed as platlib.
* Adds `cmdclass` overrides for `build` and `install`.

2.6 (Sept 2022)
---------------

* Avoid mutable default arguments
* Workaround probable `bug <https://github.com/mdavidsaver/setuptools_dso/issues/23>`_ in `setuptools >= 63.4.3 <https://github.com/pypa/setuptools/issues/3591>`_

2.5 (Jan 2022)
--------------

* Add :py:attr:`ProbeToolchain.info` and :py:class:`probe.ToolchainInfo` for :ref:`probe_classify`.
* Add :py:meth:`ProbeToolchain.eval_macros`

2.4 (Oct 2021)
--------------

* More logging from DSO search process.
* Add setuptools as runtime dependency. (Edmund Blomley)

2.3 (Aug 2021)
--------------

* Strip out "-flto" when doing probe compiles with GCC and Clang.
  Fixes :py:meth:`setuptools_dso.ProbeToolchain.sizeof` size extraction.

2.2 (Aug 2021)
--------------

* Add informational prints to :py:class:`setuptools_dso.ProbeToolchain` methods.
* :py:func:`setuptools_dso.setup` demote error to warning if 'bdist_wheel' already overridden.

2.1 (July 2021)
---------------

* Introduce usage of **$SETUPTOOLS_DSO_PLAT_NAME** to override platform name during wheel builds
* Add :py:class:`setuptools_dso.ProbeToolchain` for toolchain introspection.
* Allow :py:func:`setuptools_dso.setup` argument x_dsos= to be a one argument callable returning a list of DSO instances.
* Correctly note that wheels with DSOs are not pure.

2.0 (June 2021)
---------------

* Begin automatic generation of an "info" python module for each DSO.  (Kaleb Barrett)
* Add the :ref:`dsoinfo` API to interact with "info" modules.

1.7 (May 2020)
--------------

* Fix support for develop install (pip install -e).  (Kirill Smelkov)

1.6 (May 2020)
--------------

* Use @rpath as install_name prefix on MacOS.  (Mehul Tikekar)
* Remove usage of install_name_tool executable on MacOS.

1.5 (Jan 2020)
--------------

* Fix parallel compile on MacOS with py>=3.8.

1.4 (Jan 2020)
--------------

* Add fake cythonize() when Cython code generator not installed
* Parallel compile of DSO sources.
* build_dso: Take package_dir into account.  (Kirill Smelkov)

1.3 (Nov 2019)
--------------

* Add cythonize() wrapper
* Add "don't clobber" logic for setup() arguments.  (Kirill Smelkov)
* handle DSOs in root (not in a package)

1.2 (Aug 2019)
--------------

* include LICENSE/COPYRIGHT in dist

1.1 (Aug 2019)
--------------

* Fix inplace build.  (Kirill Smelkov)
* Fix incremental rebuild.  (Kirill Smelkov)

1.0 (Oct 2018)
--------------

* Initial stable release
