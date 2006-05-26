#!/bin/env python

import sys, re, datetime
sys.path.append ('../../')

from sqlalchemy import *
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg 
import gtk
dbg.debug(False)

eng = sk.config.spawnEngine()


zz= sqlt = SqlWidgetTreeView(tables=['euro_user','euro_mail'],
                             engine=eng, single=True)
gtk.main()


