#!/bin/sh
set -e -x

cd /io

echo "============================================================"

BASE="$PYTHONPATH"
TOP="$PWD/root"

for PYBIN in /opt/python/*/bin
do
    rm -rf "$TOP" build repo
    export PYTHONPATH="$BASE"

    # needed for isolated wheel build
    "${PYBIN}/python" -m pip download -d repo setuptools wheel

    "${PYBIN}/python" setup.py clean -a
    "${PYBIN}/python" setup.py sdist
    "${PYBIN}/python" -m pip wheel -v --no-index -f repo -w repo dist/setuptools_dso-*.tar.gz

    find .

    cd example
    rm -rf build
    "${PYBIN}/python" -m pip wheel -v --no-index -f ../repo -w ../repo .
    git status
    cd ..

    "${PYBIN}/python" -m pip install -v --no-index -f repo dsodemo
    "${PYBIN}/python" -m dsodemo.cli
done
