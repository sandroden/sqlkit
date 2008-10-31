#!/usr/bin/python

import os
import sys
import doctest

os.environ['LANG'] = 'C'

files = (
    'mask.txt',
    )

for filename in files:
    doctest.testfile(filename)

    

