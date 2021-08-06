
import re
import os
import shutil

import tempfile
try:
    from tempfile import TemporaryDirectory
except ImportError:
    class TemporaryDirectory(object):
        def __init__(self):
            self.name = tempfile.mkdtemp()
        def __del__(self):
            self.cleanup()
        def __enter__(self):
            return self.name
        def __exit__(self,A,B,C):
            self.cleanup()
        def cleanup(self):
            if self.name is not None:
                shutil.rmtree(self.name, ignore_errors=True)
                self.name = None

from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler
from distutils.errors import DistutilsExecError, CompileError
from distutils import log

__all__ = (
    'ProbeToolchain',
)

class ProbeToolchain(object):
    """Inspection of compiler

    :param bool verbose: If True, enable additional prints
    :param str compiler: If not None, select non-default compiler toolchain
    :param list headers: List of headers to include during all test compilations
    :param list define_macros: List of (macro, value) tuples to define during all test compilations
    """
    def __init__(self, verbose=False,
                 compiler=None,
                 headers=[], define_macros=[]):
        self.verbose = verbose
        self.headers = list(headers)
        self.define_macros = list(define_macros)

        self.compiler = new_compiler(compiler=compiler,
                                     verbose=self.verbose,
                                     dry_run=False,
                                     force=True)
        customize_compiler(self.compiler)
        # TODO: quiet compile errors?

        # clang '-flto' produces LLVM bytecode instead of ELF object files.
        # LLVM has a funny encoding for string constants which is hard to
        # parse for sizeof() detecton.  So we omit '-flto' for test compiles
        for name in ('compiler', 'compiler_so', 'compiler_cxx') + ('compile_options', 'compile_options_debug'):
            ccmd = getattr(self.compiler, name, None)
            if ccmd is not None:
                ccmd = [arg for arg in ccmd if arg!='-flto']
                setattr(self.compiler, name, ccmd)

        self._tdir = TemporaryDirectory()
        self.tempdir = self._tdir.name

    def compile(self, src, language='c', define_macros=[], **kws):
        """Compile provided source code and return path to resulting object file

        :returns: Path string to object file in temporary location.
        :param str src: Source code string
        :param str language: Source code language: 'c' or 'c++'
        :param list define_macros: Extra macro definitions.
        :param list include_dirs: Extra directories to search for headers
        :param list extra_compile_args: Extra arguments to pass to the compiler
        """
        define_macros = self.define_macros + list(define_macros)

        for ext, lang in self.compiler.language_map.items():
            if lang==language:
                srcname = os.path.join(self.tempdir, 'try_compile' + ext)
                break
        else:
            raise ValueError('unknown language '+language)

        log.debug('/* test compile */\n'+src)
        with open(srcname, 'w') as F:
            F.write(src)

        objs = self.compiler.compile([srcname],
                                    output_dir=self.tempdir,
                                    macros=define_macros,
                                    **kws
                                    )
        assert len(objs)==1, (srcname, objs)

        return objs[0]

    def try_compile(self, src, **kws):
        """Return True if provided source code compiles

        :param str src: Source code string
        :param str language: Source code language: 'c' or 'c++'
        :param list define_macros: Extra macro definitions.
        :param list include_dirs: Extra directories to search for headers
        :param list extra_compile_args: Extra arguments to pass to the compiler
        """
        try:
            self.compile(src, **kws)
            return True
        except (DistutilsExecError, CompileError) as e:
            return False

    def check_includes(self, headers, **kws):
        """Return true if all of the headers may be included (in order)

        :param list headers: List of header file names
        :param str language: Source code language: 'c' or 'c++'
        :param list define_macros: Extra macro definitions.
        :param list include_dirs: Extra directories to search for headers
        :param list extra_compile_args: Extra arguments to pass to the compiler
        """
        src = ['#include <%s>'%h for h in self.headers+list(headers)]

        ret = self.try_compile('\n'.join(src), **kws)
        log.info('Probe includes %s -> %s', headers, 'Present' if ret else 'Absent')
        return ret

    def check_include(self, header, **kws):
        """Return true if the header may be included

        :param str header: Header file name
        :param str language: Source code language: 'c' or 'c++'
        :param list define_macros: Extra macro definitions.
        :param list include_dirs: Extra directories to search for headers
        :param list extra_compile_args: Extra arguments to pass to the compiler
        """
        return self.check_includes([header], **kws)

    def sizeof(self, typename, headers=(), **kws):
        """Return size in bytes of provided typename

        :param str typename: Header file name
        :param list headers: List of headers to include during all test compilations
        :param str language: Source code language: 'c' or 'c++'
        :param list define_macros: Extra macro definitions.
        :param list include_dirs: Extra directories to search for headers
        :param list extra_compile_args: Extra arguments to pass to the compiler
        """
        # borrow a trick from CMake.  see Modules/CheckTypeSize.c.in
        src = ['#include <%s>'%h for h in self.headers+list(headers)]
        src += [
            '#define PROBESIZE (sizeof(%s))'%typename,
            "char probe_info[] = {'P','R','O','B','E','I','N','F','O','[',"
            "  ('0'+((PROBESIZE/10000)%10)),"
            "  ('0'+((PROBESIZE/1000)%10)),"
            "  ('0'+((PROBESIZE/100)%10)),"
            "  ('0'+((PROBESIZE/10)%10)),"
            "  ('0'+((PROBESIZE/1)%10)),"
            "']'};",
            ""
        ]

        obj = self.compile('\n'.join(src), **kws)

        with open(obj, 'rb') as F:
            raw = F.read()

        if raw.find(b'\x01\x01\x01P\x01\x01\x01R\x01\x01\x01O\x01\x01\x01B\x01\x01\x01E\x01\x01\x01I\x01\x01\x01N\x01\x01\x01F\x01\x01\x01O')!=-1:
            # MSVC
            raw = raw.replace(b'\x01\x01\x01', b'')

        M = re.match(b'.*PROBEINFO\\[(\\d+)\\].*', raw, re.DOTALL)
        if M is None:
            print(repr(raw))
            raise RuntimeError('Unable to find PROBEINFO for %s'%typename)

        size = int(M.group(1))
        log.info('Probe sizeof(%s) = %d', typename, size)

        return size

    def check_symbol(self, symname, headers=(), **kws):
        """Return True if symbol name (macro, variable, or function) is defined/delcared

        :param str symname: Symbol name
        :param list headers: List of headers to include during all test compilations
        :param str language: Source code language: 'c' or 'c++'
        :param list define_macros: Extra macro definitions.
        :param list include_dirs: Extra directories to search for headers
        :param list extra_compile_args: Extra arguments to pass to the compiler
        """
        src = ['#include <%s>'%h for h in self.headers+list(headers)]
        src += [
            'void* probe_symbol(void) {',
            '#if defined(%s)'%symname,
            '  return 0;',
            '#else',
            '  return (void*)&%s;'%symname,
            '#endif',
            '}',
            ''
        ]

        ret = self.try_compile('\n'.join(src), **kws)
        log.info('Probe Symbol %s -> %s', symname, 'Present' if ret else 'Absent')
        return ret

    def check_member(self, struct, member, headers=(), **kws):
        """Return True if the given structure has the named member

        :param str struct: Structure name
        :param str member: Member name
        :param list headers: List of headers to include during all test compilations
        :param str language: Source code language: 'c' or 'c++'
        :param list define_macros: Extra macro definitions.
        :param list include_dirs: Extra directories to search for headers
        :param list extra_compile_args: Extra arguments to pass to the compiler
        """
        src = ['#include <%s>'%h for h in self.headers+list(headers)]
        src += [
            'int probe_member(void) {',
            '  return (int)sizeof( ((%s *)0)->%s); '%(struct, member),
            '}',
            ''
        ]

        ret = self.try_compile('\n'.join(src), **kws)
        log.info('Probe Member %s::%s -> %s', struct, member, 'Present' if ret else 'Absent')
        return ret
