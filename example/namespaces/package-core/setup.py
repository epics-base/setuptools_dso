from setuptools import setup
kwargs = {
    "name" : "test-dso-nsp-core",
    "version" : "0.0.1",
    "install_requires" : [],
    "packages" : ["testnsp", "testnsp.testcore"],
}

setup(**kwargs)
