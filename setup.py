#!/usr/bin/python

"""
Name: sqlkit
Author: Sandro Dentella
Author-email: sandro at e-den it
Home-page: sqlkit.argolinux.org
Download-url: http://sqlkit.argolinux.org/download/
License: GPL v3
Keywords: database gui gtk package
Platform: Linux, Windows, Mac
Requires: babel
Requires: dateutils
Requires: sqlalchemy (>= 0.5)
Provides: sqlkit
"""

classifiers = """\
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: End Users/Desktop
License :: OSI Approved :: GNU Affero General Public License v3
Operating System :: MacOS
Operating System :: Microsoft
Operating System :: OS Independent
Operating System :: POSIX
Operating System :: POSIX :: Linux
Programming Language :: Python
Topic :: Database :: Front-Ends
Topic :: Software Development :: Libraries
Topic :: Software Development :: Libraries :: Application Frameworks
Topic :: Software Development :: Libraries :: Python Modules"""

import os
import sys
try:
   from setuptools import setup, find_packages
except ImportError, e:
   print "You need to install setuptools to use this setup.py script"
   sys.exit(1)


f = open('sqlkit/__init__.py')
for line in f:
   if line.startswith('__version__'):
       version = line.split()[2].strip("'")

try:
   import pygtk
   pygtk.require('2.0')
except:
   print "You need to install also pygtk and I was not able to work out"
   print "  a correct dependency in setup.py"
   sys.exit(1)
   
setup(name='sqlkit',
      version=version,
      description="""GUI to edit databases. Many backend supported (Postgres, Sqlite, MySql,...).
Based on python, GTK, sqlalchemy. It's split into a GUI and a very rich package to create
database interfaces""",
      author='Alessandro Dentella',
      author_email='sandro@e-den.it',
      url='http://sqlkit.argolinux.org/',
      install_requires=['sqlalchemy >= 0.5', 'Babel', 'python-dateutil'],
      packages = find_packages('.'),
      scripts=['bin/sqledit'],
#      package_dir = {'' : 'sqlkit'},
#      package_data = {'sqlkit' : ['locale']},
      classifiers= __doc__.split('\n'),
      include_package_data=True,      
     )

