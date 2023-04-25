from __future__ import print_function

import dsodemo.ext.dtest  # preload dsodemo.lib.demo dso which dsodemo.ext.dtest uses

from . import ext

def main():
    print('via .ext -> dsodemo.lib.demo:')
    print(ext.dsodemo_foo())
    print(ext.dsodemo_bar())

if __name__ == '__main__':
    main()
