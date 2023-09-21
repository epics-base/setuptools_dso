from setuptools_dso import DSO, Extension, setup
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
    "packages" : ["testnsp", "testnsp.testdso"],
}

setup(
    **kwargs,
    ext_modules = [theext],
    x_dsos = [thedso],
)
