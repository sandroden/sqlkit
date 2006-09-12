#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
import sqlkit as sk
import dbg 
dbg.DBG = 1

from sqlalchemy import *
from layout import *
#from validator import Validator

engine = sk.config.new_engine(echo=False)
map_labels(filename='label_map.txt')


zz = sk.mask.SqlMask (tables='euro_user', engine=engine)
#zz.sqlData.printall(mode='dict')

gtk.main()


