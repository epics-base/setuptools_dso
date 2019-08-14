#!/bin/sh
set -e

die() {
    echo "$@" 1>&2
    exit 1
}

[ -d src/setuptools_dso ] || exit 2

PYTHON="$1"
[ "$PYTHON" ] || PYTHON=python

rm -rf env

virtualenv env

. env/bin/activate

"$PYTHON" setup.py clean -a
"$PYTHON" setup.py -v install

# inplace build
echo -e '\n* inplace build\n'
cd example
"$PYTHON" setup.py clean -a
git clean -fdx	# `setup.py clean` does not clean inplace built files
"$PYTHON" -m dsodemo.cli 2>/dev/null && die "error: worktree must be clean"
"$PYTHON" setup.py -v build_dso -i
"$PYTHON" setup.py -v build_dso -i -f  # incremental recompile
"$PYTHON" setup.py -v build_ext -i
"$PYTHON" -m dsodemo.cli


# build + install
echo -e '\n* build + install\n'
"$PYTHON" setup.py clean -a
git clean -fdx
"$PYTHON" -m dsodemo.cli 2>/dev/null && die "error: worktree must be clean"
"$PYTHON" setup.py -v install

cd ..

"$PYTHON" -m dsodemo.cli
