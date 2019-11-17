#!/bin/sh
set -e -x

# https://github.com/joerick/cibuildwheel/blob/master/cibuildwheel/macos.py

curl -L -o /tmp/Python.pkg $URL
curl -L -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py

sudo installer -pkg /tmp/Python.pkg -target /

export PATH=$PATH:/Library/Frameworks/Python.framework/Versions/$PYVER/bin

which $PYTHON

$PYTHON --version

$PYTHON /tmp/get-pip.py --no-setuptools --no-wheel

$PYTHON -m pip --version
$PYTHON -m pip install --upgrade setuptools
$PYTHON -m pip install --upgrade wheel


"$PYTHON" setup.py clean -a
"$PYTHON" setup.py sdist
"$PYTHON" setup.py -v install

cd example

"$PYTHON" setup.py clean -a
"$PYTHON" setup.py -v install

cd ..

"$PYTHON" -m dsodemo.cli
