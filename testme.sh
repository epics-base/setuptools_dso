#!/bin/sh
set -e

[ -d src/setuptools_dso ] || exit 2

rm -rf env

virtualenv env

. env/bin/activate

python setup.py clean -a
python setup.py -v install

cd example

python setup.py clean -a
python setup.py -v install

cd ..

python -m dsodemo.cli
