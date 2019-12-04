
from __future__ import print_function

import sys, os

def fixpath():
    path = os.environ.get('PATH', '').split(os.pathsep)
    moddir = os.path.dirname(__file__)
    path.append(os.path.join(moddir, 'lib'))
    os.environ['PATH'] = os.pathsep.join(path)

if sys.platform == "win32":
    fixpath()

from .ext import dtest

if __name__=='__main__':
    print(dtest.foo())
    print(dtest.bar())
