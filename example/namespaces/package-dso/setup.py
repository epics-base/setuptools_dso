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
setup(
    ext_modules = [theext],
    x_dsos = [thedso],
)
