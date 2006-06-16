#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import sys, re, datetime
sys.path.append ('../../')
from sqlalchemy import *
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg 
import gtk
dbg.debug(True)
#dbg.debug(False)

#eng = sk.config.spawnEngine(file='erm.ini')
eng = sk.config.spawnEngine(file='test.ini')

table='euro_user'
#table='jobs'
zz= sqlt = sk.SqlTable(table=table, engine=eng, single=True,
                             geom=(-1,360))
# , noup=['user_age']
#zz.w['Window'].set_geometry_hints(None, base_width=300, base_height=200)
zz.w['Window'].set_geometry_hints(None, min_width=400, min_height=200)

zz.order_by = 'user_address'
gtk.main()


