#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import sys, re, datetime
sys.path.append ('../../')
from planning import plan
from sqlalchemy import *
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg 
import gtk
dbg.debug(True)
#dbg.debug(False)

#eng = sk.config.spawnEngine(file='erm.ini')
eng = sk.config.spawnEngine()

table='euro_user'
#table='jobs'
zz= sqlt = SqlWidgetTreeView(table=table, engine=eng, single=True)
zz.order_by = 'user_address'
gtk.main()


