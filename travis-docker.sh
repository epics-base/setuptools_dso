#!/bin/sh
set -e -x

cd /io

echo "============================================================"

BASE="$PYTHONPATH"
TOP="$PWD/root"

for PYBIN in /opt/python/*/bin
do
    rm -rf "$TOP"
    export PYTHONPATH="$BASE"

    rm -rf build
    "${PYBIN}/python" setup.py clean -a
    "${PYBIN}/python" setup.py sdist

    find .

    "${PYBIN}/python" setup.py install --root "$TOP"

    find "$TOP" -name setuptools_dso
    export PYTHONPATH="$BASE:$(dirname $(find "$TOP" -name setuptools_dso ))"

    cd example
    rm -rf build
    "${PYBIN}/python" setup.py clean -a
    "${PYBIN}/python" setup.py install --single-version-externally-managed --root "$TOP"
    cd ..
    "${PYBIN}/python" -m dsodemo.cli
done
