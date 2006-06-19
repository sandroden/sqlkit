#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import sys, re, datetime
sys.path.append ('../../')
#from planning import plan
from sqlalchemy import *
import sqlkit as sk
import dbg 
import gtk
dbg.debug(True)
#dbg.debug(False)
import sqlalchemy
#import sqlalchemy.mods
#import sqlalchemy.mods.threadlocal

eng = sk.config.new_engine(globalconn=True)
#meta = default_metadata
session = create_session()
dbg.write(session)
#eng = create_engine('postgres://test:vicie@localhost:5433/test')

#meta =  BoundMetaData(eng)

table='euro_user'
#table='jobs'
zz = sqlt = sk.SqlTable(table=table, session=session)

# , noup=['user_age']
#zz.w['Window'].set_geometry_hints(None, base_width=300, base_height=200)
zz.w['Window'].set_geometry_hints(None, min_width=400, min_height=200)

zz.order_by = 'user_address'
eng.echo = True
gtk.main()


