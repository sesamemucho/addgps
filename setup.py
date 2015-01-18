# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.org') as f:
    readme = f.read()

with open('license.txt') as f:
    license = f.read()

setup(
    name='addgps',
    version='0.2.0',
    description='Add GPS location to EXIF files',
    long_description=readme,
    author='Bob Forgey',
    author_email='sesamemucho@gmail.com',
    url='https://github.com/sesamemucho/addgps',
    license=license,
    packages=find_packages(exclude=())
)
