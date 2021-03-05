
from __future__ import print_function

import ctypes

from .ext import dtest
from .lib import demo_dsoinfo

def main():
    print(dtest.foo())
    print(dtest.bar())
    # ctypes.RTLD_GLOBAL ensures we don't load a second instance.
    demolib = ctypes.CDLL(demo_dsoinfo.sofilename, ctypes.RTLD_GLOBAL)
    myvar = ctypes.c_int.in_dll(demolib, 'myvar')
    dtest.check_myvar(ctypes.addressof(myvar))

if __name__=='__main__':
    main()
