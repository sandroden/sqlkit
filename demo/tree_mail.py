#!/bin/env python

import sys, re, datetime
sys.path.append ('../../')

from sqlalchemy import *
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg 
import gtk
dbg.debug(True)

eng = sk.config.spawnEngine()


zz= sqlt = SqlWidgetTreeView(table='euro_mail', engine=eng, single=True)
gtk.main()


