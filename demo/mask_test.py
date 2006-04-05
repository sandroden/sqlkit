#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path, config, reflect, mask
import sd
sd.dbg = 1

from sqlalchemy import *
from layout import *
from validator import Validator
#from SqlTreeView import *
#import sqlfilter

engine = config.spawnEngine(echo=False)
cursor = engine.connection().cursor()
#print cursor.cursor.description
#user_table = reflect.mapTable (engine, 'euro_user')
user_table = Table ('euro_user', engine, autoload=True)
#user_mapper = reflect.getMapper (user_table)
class Mapper(object):
    pass
user_mapper = mapper (Mapper, user_table)
c = user_table.c
#print cursor.description


#print dir(user_mapper.select)
#user_record = reflect.getRecord (user_mapper, user_id = 1)
#ui = user_table.c.user_id 
#print ui.__eq__
#user_record = user_mapper.get_by (ui = 1)
#user_records = result
#print user_records[0]
#sys.exit()


sql_text = "user_id > 5"
user_mask = mask.SqlMask (mapper=user_mapper,
                          records = None, debug=1, sql=sql_text)
#user_mask.record_forward(1)
gtk.main()


