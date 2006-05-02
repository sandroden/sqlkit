#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../..')
import sqlkit as sk
import dbg
dbg.DBG = 1

from sqlalchemy import *
from layout import *
#from validator import Validator

engine = sk.config.spawnEngine(echo=False)
user_table = Table('euro_mail', engine, autoload=True)
class Mails(object): pass
user_mapper = mapper (Mails, user_table)

#sql_text = "user_id > 5"
user_mask = sk.mask.SqlMask (mapper=user_mapper)

gtk.main()


