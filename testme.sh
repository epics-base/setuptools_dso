#!/bin/sh
set -e

[ -d src/setuptools_dso ] || exit 2

PYTHON="$1"
[ "$PYTHON" ] || PYTHON=python

rm -rf env

virtualenv env

. env/bin/activate

"$PYTHON" setup.py clean -a
"$PYTHON" setup.py -v install

cd example

"$PYTHON" setup.py clean -a
"$PYTHON" setup.py -v install

cd ..

"$PYTHON" -m dsodemo.cli
