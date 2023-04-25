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
(cd project2/src && python -m use_dsodemo.cli 2>/dev/null) && die "error: worktree must be clean"
python setup.py -v build_dso -i
python setup.py -v build_dso -i -f  # incremental recompile
python setup.py -v build_ext -i
X="`pwd`/src"
cd project2
PYTHONPATH=$X python setup.py -v build_ext -i
cd ..
(cd src && python -m dsodemo.cli)
(cd project2/src && PYTHONPATH=$X python -m use_dsodemo.cli)


# build + install
echo -e '\n* build + install\n'
python setup.py clean -a
git clean -fdx
python -m dsodemo.cli 2>/dev/null && die "error: worktree must be clean"
python -m use_dsodemo.cli 2>/dev/null && die "error: worktree must be clean"
pip install --no-build-isolation -v .
# --no-use-pep517 is used to workaround https://github.com/pypa/setuptools/issues/1694 on py36 and py35
cd project2
pip install --no-build-isolation --no-use-pep517 -v .

cd ../..
python -m dsodemo.cli
python -m use_dsodemo.cli


# install in development mode
pip uninstall -y dsodemo
pip uninstall -y use_dsodemo
python -m dsodemo.cli 2>/dev/null && die "error: dsodemo not uninstalled"
python -m use_dsodemo.cli 2>/dev/null && die "error: dsodemo not uninstalled"

cd example
python setup.py clean -a
git clean -fdx
(cd src && python -m dsodemo.cli 2>/dev/null) && die "error: worktree must be clean"
(cd project2/src && python -m use_dsodemo.cli 2>/dev/null) && die "error: worktree must be clean"
pip install --no-build-isolation -v -e .
cd project2
pip install --no-build-isolation --no-use-pep517 -v -e .

cd ../..
python -m dsodemo.cli
python -m use_dsodemo.cli
