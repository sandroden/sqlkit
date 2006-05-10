#!/usr/bin/env python

import sys

sys.path.append ('../../')
import sqlkit as sk
import dbg
import gtk

from sqlalchemy import *

engine = sk.config.spawnEngine(echo=False)
user_table = Table ('euro_user', engine, autoload=True)

class Mapper(object):
    pass
user_mapper = mapper (Mapper, user_table)

sql_text = "user_id > 5"
zz = user_mask = sk.SqlMask (mapper=user_mapper, sql=sql_text)

gtk.main()


