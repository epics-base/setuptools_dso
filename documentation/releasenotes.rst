.. _releasenotes:

Release Notes
=============

2.1 (UNRELEASED)
----------------

* Introduce usage of **$SETUPTOOLS_DSO_PLAT_NAME** to override platform name during wheel builds
* Add :py:class:`setuptools_dso.ProbeToolchain` for toolchain introspection.
* Allow setup() argument x_dsos= to be a one argument callable returning a list of DSO instances.
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
