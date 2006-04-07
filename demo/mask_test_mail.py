#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path, config, reflect, mask
import sd
sd.dbg = 1

from sqlalchemy import *
from layout import *
from validator import Validator

engine = config.spawnEngine(echo=False)
cursor = engine.connection().cursor()
user_table = Table('euro_mail', engine, autoload=True)
class Mails(object): pass
user_mapper = mapper (Mails, user_table)

#sql_text = "user_id > 5"
user_mask = mask.SqlMask (mapper=user_mapper,
                          records = None, debug=1, sql=None)

gtk.main()


