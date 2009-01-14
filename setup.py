#!/usr/bin/python


from setuptools import setup, find_packages
import os

setup(name='sqlkit',
      version='0.8.5-pre',
      description='GUI library for database editing',
      author='Alessandro Dentella',
      author_email='sandro@e-den.it',
      url='http://sqlkit.argolinux.org/',
#      package_dir={'':'sqlkit'},
      packages=find_packages('.', exclude=''),
#     packages=find_packages('lib', exclude=['ez_setup', 'examples', 'tests']),
#      packages=find_packages('lib', exclude='isi.egg-info'),
      scripts=['bin/sqledit']
     )

