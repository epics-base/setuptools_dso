
from __future__ import print_function

import ctypes

from setuptools_dso import find_dso

from .ext import dtest

def main():
    print(dtest.foo())
    print(dtest.bar())
    # ctypes.RTLD_GLOBAL ensures we don't load a second instance.
    demolib = ctypes.CDLL(find_dso('dsodemo.lib.demo', so=True), ctypes.RTLD_GLOBAL)
    myvar = ctypes.c_int.in_dll(demolib, 'myvar')
    dtest.check_myvar(ctypes.addressof(myvar))

if __name__=='__main__':
    main()
