#!/bin/env python

import sys, re, datetime
sys.path.append ('../../')

from sqlalchemy import *
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg 
import gtk
dbg.debug(True)

eng = sk.config.spawnEngine(globalconn=True)


zz= sqlt = SqlWidgetTreeView(table='euro_mail', single=True,
                             order_by='mail_address')
gtk.main()


