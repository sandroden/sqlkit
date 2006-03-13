#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path, config, reflect, mask_sd

from sqlalchemy import *
from layout import *
from validator import Validator
from SqlTreeView import *

engine = config.spawnEngine()

user_table = reflect.mapTable (engine, 'euro_user')
user_mapper = reflect.getMapper (user_table)
user_record = reflect.getRecord (user_mapper, user_id = 1)

user_mask = mask_sd.SqlMask (mapper=user_mapper,
                          table=user_table,
                          record = user_record)

gtk.main()


