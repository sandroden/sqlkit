#!/usr/bin/python

import os
import sys
import doctest

import sys
import babel


os.environ['LANG'] = 'C'
os.environ['LANG'] = 'en_US.utf8'
doctest.ELLIPSIS = 10

files = (
    'completions.txt',
    'dates.txt',
    'defaults.txt',
    'django2sa.txt',
    'fields.txt',
    'filters.txt',
    'mapper_inspect.txt',
    'mask.txt',
    )

if sys.argv[1:]:
    files = sys.argv[1:]

for filename in files:
    print filename
    os.environ['LANG'] = 'en_US.utf8'
    doctest.testfile(filename, optionflags=doctest.ELLIPSIS)

    

