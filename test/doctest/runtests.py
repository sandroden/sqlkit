#!/usr/bin/python

import os
import sys
import doctest

import sys
if sys.argv:
    files = sys.argv

os.environ['LANG'] = 'C'

files = (
    'mask.txt',
    'dates.txt',
    )

for filename in files:
    doctest.testfile(filename)

    

