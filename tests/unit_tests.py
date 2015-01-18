#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2015-01-16 17:05:57 bob>

## invoke tests using following command line:
## PYTHONPATH=".:" tests/unit_tests.py --verbose

import unittest
import addgps

class TestMethods(unittest.TestCase):

    def setUp(self):
        pass

    def test_easy_alias(self):
        a = addgps.handle_aliases(("x=33.3, 44.4",))
        self.assertEqual(a, {'x': ("33.3", "44.4")})

    def test_neg_alias(self):
        a = addgps.handle_aliases(("x=-33.3, -44.4",))
        self.assertEqual(a, {'x': ("-33.3", "-44.4")})

    def test_alias_nospace(self):
        a = addgps.handle_aliases(("x=33.3,44.4",))
        self.assertEqual(a, {'x': ("33.3", "44.4")})

    def test_alias_morespace(self):
        a = addgps.handle_aliases((" x = 33.3 , 44.4 ",))
        self.assertEqual(a, {'x': ("33.3", "44.4")})

    def test_two_alias(self):
        a = addgps.handle_aliases(("x=33.3, 44.4","yy=66.6, 77.7"))
        self.assertEqual(a, {'x': ("33.3", "44.4"), 'yy': ("66.6", "77.7")})

    def test_NE_alias(self):
        a = addgps.handle_aliases(("x=33.3N, 44.4E",))
        self.assertEqual(a, {'x': ("33.3N", "44.4E")})

    def test_bad_short_alias(self):
        with self.assertRaisesRegexp(ValueError, r'Unrecognized alias .*'):
            addgps.handle_aliases(("x=33.3N",))

    def test_bad_short_alias2(self):
        with self.assertRaisesRegexp(ValueError, r'Unrecognized alias .*'):
            addgps.handle_aliases(("x=33.3N, ",))

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
