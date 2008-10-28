#!/usr/bin/python


from setuptools import setup, find_packages
import os

setup(name='sqlkit',
      version='0.8.3-pre',
      description='GUI library for database editing',
      author='Alessandro Dentella',
      author_email='sandro@e-den.it',
      url='http://sqlkit.e-den.it/',
#      package_dir={'':'sqlkit'},
      packages=find_packages('.', exclude=''),
#     packages=find_packages('lib', exclude=['ez_setup', 'examples', 'tests']),
#      packages=find_packages('lib', exclude='isi.egg-info'),
      scripts=['bin/sqledit']
     )

