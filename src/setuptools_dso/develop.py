# Copyright 2022  Michael Davidsaver
# SPDX-License-Identifier: BSD
# See LICENSE

import sys
import os
from distutils import log
from distutils.dir_util import mkpath

from setuptools import Command
from setuptools.command.develop import develop as _develop

class link_develop(Command):
    """
    Use of .egg-link (really 'easy-install.pth') doesn't work in conjunction with RPATH.
    Further, simply sym-linking directories into the install tree doesn't work as path
    traversal follows sym-links.  eg. "adir/link2dir/../other/lib" does not reach "adir/other/lib".

    So instead, we hijack the develop command entirely to install sym-links for each individual
    file (.py and .so/dylib).  This is not 100% as 'develop' must be re-run each time new files
    are created in the source tree.
    """

    description = _develop.description

    # pull in the full set of options as we don't know which ones
    # pip can/will use.

    user_options = _develop.user_options
    boolean_options = _develop.boolean_options

    def initialize_options(self):
        _develop.initialize_options(self) # evil!
        self.uninstall = None
        self.no_deps = None

    def finalize_options(self):
        pass

    def run(self):
        if self.uninstall:
            self.run_uninstall()
        else:
            self.run_install()

    def run_install(self):
        log.info('setuptools_dso develop mode')

        install_lib = self.get_finalized_command('install_lib')

        # note: doc comment on get_inputs() claims the returned list is one-to-one
        #       with get_outputs().   However, this is only true if compile=False,
        #       otherwise get_outputs() emits bytecode files between .py and .so
        install_lib.compile = False

        install_lib.build()

        for inp, out in zip(install_lib.get_inputs(), install_lib.get_outputs()):
            assert os.path.basename(inp)==os.path.basename(out), (inp, out)

            outdir = os.path.dirname(out)
            inp = os.path.relpath(inp, outdir)

            mkpath(outdir, verbose=self.verbose, dry_run=self.dry_run)

            log.info('ln -s %s %s', inp, out)

            # note: samefile() follows symlinks by default
            if not (os.path.exists(out) and os.path.samefile(inp, out)) and not self.dry_run:
                os.symlink(inp, out)

        # TODO: need to create/install *.dist_info for "pip uninstall ..."
        #dist_info = self.get_finalized_command('dist_info')
        #dist_info.run()

    def run_uninstall(self):
        log.info('setuptools_dso develop mode, uninstall')

        install_lib = self.get_finalized_command('install_lib')
        # leave install_lib.compile (maybe) set so that bytecode is also removed

        # From an abundance of caution, only removing known output files
        # and empty directories containing them.

        pkgdirs = set()
        for out in install_lib.get_outputs():
            pkgdirs.add(os.path.dirname(out))
            if os.path.isfile(out):
                log.info('rm %s', out)
                if not self.dry_run:
                    os.remove(out)

        # delete (longer) sub-directories first
        pkgdirs = list(pkgdirs)
        pkgdirs.sort()
        pkgdirs.reverse()

        for odir in pkgdirs:
            if os.path.isdir(odir):
                try:
                    if not self.dry_run:
                        os.rmdir(odir)
                except OSError as e:
                    log.warn('Unable to remove directory: %s : %s', odir, e.args)
                else:
                    log.info('rmdir %s', odir)


if sys.platform=='win32':
    develop = _develop

else:
    develop = link_develop
