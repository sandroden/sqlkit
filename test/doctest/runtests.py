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
    'mapper_inspect.txt',
    'django2sa.txt',
    )

if sys.argv[1:]:
    files = sys.argv[1:]

for filename in files:
    print filename
    doctest.testfile(filename)

    

