#!/bin/env python

import sys, re, datetime
sys.path.append ('../../')

import dbg 
if sys.platform.startswith('linux2'):
    dbg.debug(2)
    dbg.conf_class_trace(ok='SqlTable|SqlMask')
    lgm = dbg.ShowLogs(show=True)
    lgm.conf(but='set_fkey_descr|(lookup|set|get)_value|[el]ne_cb|match_func')

import gtk
from sqlalchemy import *
import sqlkit as sk

eng = sk.config.new_engine(globalconn=True)


zz= sqlt = sk.SqlTable(tables=['euro_user','euro_mail'],
                             engine=eng, single=True)
gtk.main()


