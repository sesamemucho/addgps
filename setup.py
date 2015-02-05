# -*- coding: utf-8 -*-
"""Just a typical setup.py file"""

from setuptools import setup, find_packages
import distutils
#import distutils.cmd
#import distutils.log
import os
import subprocess

def get_readme():
    """Return readme from README.org"""
    with open('README.org') as f:
        myreadme = f.read()
    return myreadme

def get_license():
    """Return license from license file"""
    with open('license.txt') as f:
        mylicense = f.read()
    return mylicense

# pylint: disable=no-name-in-module,no-member,no-init,attribute-defined-outside-init
# From seasonofcode.com:
class PylintCommand(distutils.cmd.Command):
    """Run pylint on all python files"""
    description = 'run pylint on addgps.py'
    user_options = [
        ('pylnt-rcfile=', None, 'path to Pylint config file'),
        ]

    def initialize_options(self):
        """Set default values for options."""
        self.pylint_rcfile = '.pylintrc'

    def finalize_options(self):
        """Post-process options."""
        if self.pylint_rcfile:
            assert os.path.exists(self.pylint_rcfile), (
                'Pylint config file %s does not exist.' % self.pylint_rcfile)

    def run(self):
        """Run command."""
        command = ['pylint']    # Pick up the virtualenv one
        if self.pylint_rcfile:
            command.append('--rcfile=%s' % self.pylint_rcfile)

        # If all files wanted:
        # command.append(os.getcwd())
        command.append(os.path.join(os.getcwd(), 'addgps.py'))
        command.append(os.path.join(os.getcwd(), 'setup.py'))

        self.announce(
            'Running command: %s' % str(command),
            level=distutils.log.INFO)
        # subprocess.check_call(command)
        subprocess.call(command)


setup(
    cmdclass={
        'pylint': PylintCommand,
        },
    name='addgps',
    version='0.2.0',
    description='Add GPS location to EXIF files',
    long_description=get_readme(),
    author='Bob Forgey',
    author_email='sesamemucho@gmail.com',
    url='https://github.com/sesamemucho/addgps',
    license=get_license(),
    packages=find_packages(exclude=())
)
