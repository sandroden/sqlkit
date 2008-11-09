#!/usr/bin/python

import os
import sys
import doctest

import sys

os.environ['LANG'] = 'C'

files = (
    'mask.txt',
    'dates.txt',
    'fields.txt',
    )

if sys.argv[1:]:
    files = sys.argv[1:]

for filename in files:
    print filename
    doctest.testfile(filename)

    

