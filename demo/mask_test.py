#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path

from sqlalchemy import *
from layout import *
from SqlTreeView import *
import reflect
import config

eng = config.spawnEngine()

#user = reflect.mapTable(engine,'euro_user')
#mail = reflect.mapTable(engine,'euro_mail')
#res = join(user, mail).select().execute()

#gtk.main()



