#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2015-01-16 17:05:57 bob>

## invoke tests using following command line:
## PYTHONPATH=".:" tests/unit_tests.py --verbose
from __future__ import print_function
import unittest
import addgps
import tempfile
import os
import subprocess
import shutil
import stat

here = os.getcwdu()

def does_file_have_gps_tags(filename):
    retval = subprocess.check_output(
        ['exiftool',
         '-GPS*',
         filename])
    
    return retval != ""

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

class TestGPSValues(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGoodLatitude(self):
        a = addgps.GPSLatitude("33.3")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "N")

        a = addgps.GPSLatitude("-33.3")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "S")

        a = addgps.GPSLatitude("33.3N")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "N")

        a = addgps.GPSLatitude("33.3S")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "S")

    def testBadGPSLat(self):
        with self.assertRaisesRegexp(ValueError, r'Negative value cannot have .*'):
            a = addgps.GPSLatitude("-44.2N")

        with self.assertRaisesRegexp(ValueError, r'Negative value cannot have .*'):
            a = addgps.GPSLatitude("-44.2S")

        with self.assertRaisesRegexp(ValueError, r'Unrecognized latitude value .*'):
            a = addgps.GPSLatitude("-cat")

        with self.assertRaisesRegexp(ValueError, r'Latitude value is out of range: .*'):
            a = addgps.GPSLatitude("93.4")

    def testGoodLongitude(self):
        a = addgps.GPSLongitude("33.3")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "W")

        a = addgps.GPSLongitude("-33.3")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "E")

        a = addgps.GPSLongitude("33.3W")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "W")

        a = addgps.GPSLongitude("33.3E")
        self.assertAlmostEqual(a.value(), 33.3)
        self.assertEqual(a.ref(), "E")

    def testBadGPSLong(self):
        with self.assertRaisesRegexp(ValueError, r'Negative value cannot have .*'):
            a = addgps.GPSLongitude("-44.2W")

        with self.assertRaisesRegexp(ValueError, r'Negative value cannot have .*'):
            a = addgps.GPSLongitude("-44.2E")

        with self.assertRaisesRegexp(ValueError, r'Unrecognized longitude value .*'):
            a = addgps.GPSLongitude("-cat")

        with self.assertRaisesRegexp(ValueError, r'Longitude value is out of range: .*'):
            a = addgps.GPSLongitude("188.0")

class TestFiles(unittest.TestCase):
    tempdir = None
    datadir = os.path.join(here, 'data')

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)
        #print("\ntemporary directory: " + self.tempdir)
        shutil.copy(os.path.join(self.datadir, "saturn.jpg"), "./")
        #print(subprocess.check_output(['ls', '-l', 'saturn.jpg']))
        os.chmod("saturn.jpg", stat.S_IRUSR|stat.S_IWUSR)
        #print(subprocess.check_output(['ls', '-l', 'saturn.jpg']))

    def create_tmp_file(self, name):
        open(os.path.join(self.tempdir, name), 'w')

    def test_addgps(self):
        self.assertFalse(does_file_have_gps_tags("saturn.jpg"))
        addgps.add_gps_to_file("saturn.jpg", 33.2, 44.4, False)
        self.assertTrue(does_file_have_gps_tags("saturn.jpg"))

    def test_removegps(self):
        self.assertFalse(does_file_have_gps_tags("saturn.jpg"))
        addgps.add_gps_to_file("saturn.jpg", 33.2, 44.4, False)
        self.assertTrue(does_file_have_gps_tags("saturn.jpg"))
        addgps.remove_gps_from_file("saturn.jpg", False)
        self.assertFalse(does_file_have_gps_tags("saturn.jpg"))

    def tearDown(self):

        shutil.rmtree(self.tempdir)

if __name__ == '__main__':
    unittest.main()
