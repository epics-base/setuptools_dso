from setuptools import setup, find_namespace_packages
kwargs = {
    "name" : "test-dso-nsp-core",
    "version" : "0.0.1",
    "install_requires" : [],
    "packages" : find_namespace_packages(include = ["testnsp.testcore", "testnsp.testcore.*"]),
}

setup(**kwargs)
