#!/bin/env python

import sys, re, datetime
sys.path.append ('../../')

from sqlalchemy import *
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg 
import gtk

eng = sk.config.spawnEngine()


sqlt = SqlWidgetTreeView(table='euro_user', engine=eng, single=True)
gtk.main()


