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


mask.SqlMask (sql="user_id > 5", table='euro_user', engine=engine)

gtk.main()


