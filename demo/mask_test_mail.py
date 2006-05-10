#!/usr/bin/env python

import sys

sys.path.append ('../../')
import sqlkit as sk
import dbg
import gtk

from sqlalchemy import *

engine = sk.config.spawnEngine(echo=False)
user_table = Table ('euro_mail', engine, autoload=True)

class Mapper(object):
    pass
user_mapper = mapper (Mapper, user_table)

zz = user_mask = sk.SqlMask (mapper=user_mapper)

gtk.main()


