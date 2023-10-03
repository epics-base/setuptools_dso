from setuptools_dso import DSO, Extension, setup
from setuptools import find_namespace_packages
thedso = DSO (
    "testnsp.testdso.thedso",
    ["testnsp/testdso/libtest.c"],
)
theext = Extension(
    "testnsp.testdso.thepyd",
    sources = ['testnsp/testdso/cyththing.pyx'],
    dsos = ["testnsp.testdso.thedso"],
)

kwargs = {
    "name" : "test-dso-nsp-dso",
    "version" : "0.0.1",
    "install_requires" : ["test-dso-nsp-core"],
    "packages" : find_namespace_packages(include = ["testnsp.testdso", "testnsp.testdso.*"]),
}

setup(
    **kwargs,
    ext_modules = [theext],
    x_dsos = [thedso],
)
