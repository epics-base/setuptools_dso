
import unittest

from .. import probe

class TryCompile(unittest.TestCase):
    def setUp(self):
        self.probe = probe.ProbeToolchain(verbose=True)

    def test_try_compile(self):
        self.assertTrue(self.probe.try_compile('#include <stdlib.h>'))
        self.assertFalse(self.probe.try_compile('intentionally invalid syntax'))

        self.assertTrue(self.probe.check_include('stdlib.h'))
        self.assertFalse(self.probe.check_include('no-such-header.h'))
        self.assertEqual(self.probe.sizeof('short'), 2)
        self.assertTrue(self.probe.check_symbol('RAND_MAX', headers=['stdlib.h']))
        self.assertTrue(self.probe.check_symbol('abort', headers=['stdlib.h']))
        self.assertFalse(self.probe.check_symbol('intentionally_undeclared_symbol', headers=['stdlib.h']))
