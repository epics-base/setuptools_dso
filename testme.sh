#!/bin/sh
set -e -x

die() {
    echo "$@" 1>&2
    exit 1
}

[ -d src/setuptools_dso ] || exit 2

PYTHON="$1"
[ "$PYTHON" ] || PYTHON=python

rm -rf env

"$PYTHON" -m virtualenv --no-download -p "$PYTHON" env

. env/bin/activate
which python
python --version

python setup.py clean -a
pip install -v .

# inplace build
echo -e '\n* inplace build\n'
cd example
python setup.py clean -a
git clean -fdx	# `setup.py clean` does not clean inplace built files
(cd src && python -m dsodemo.cli 2>/dev/null) && die "error: worktree must be clean"
python setup.py -v build_dso -i
python setup.py -v build_dso -i -f  # incremental recompile
python setup.py -v build_ext -i
(cd src && python -m dsodemo.cli)


# build + install
echo -e '\n* build + install\n'
python setup.py clean -a
git clean -fdx
python -m dsodemo.cli 2>/dev/null && die "error: worktree must be clean"
pip install -v .

cd ..

python -m dsodemo.cli
