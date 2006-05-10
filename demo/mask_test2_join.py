#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
import sqlkit as sk
import sqlkit.inspect as inspect
import dbg 
dbg.DBG = 1

from sqlalchemy import *
from layout import *
#from validator import Validator

engine = sk.config.spawnEngine(echo=False)
map_labels(filename='label_map.txt')

#m = join_tables(tables=['euro_user', 'euro_mail'], engine=engine)

zz = sk.mask.SqlMask (sql="user_id > 5",
                      tables=['euro_user', 'euro_mail'], engine=engine)

#zz.sqlData.printall(mode='dict')

gtk.main()


