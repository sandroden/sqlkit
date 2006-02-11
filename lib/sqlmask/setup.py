
from ez_setup import use_setuptools
use_setuptools ()
from setuptools import setup, find_packages

setup (
    name = 'sqlmask',
    version = '0.1',
    packages = find_packages ('lib'),
    package_dir = {'' : 'lib'}
    )
