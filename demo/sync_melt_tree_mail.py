#!/usr/bin/env python

import sys
sys.path.append ('../../')
import dbg
if sys.platform.startswith('linux'):
    dbg.conf_class_trace(ok='SqlTable|SqlMask')
    dbg.debug(2)
    lgm = dbg.ShowLogs(show=True)
    lgm.conf(but='set_fkey_descr|lookup_value|set_value|ene_cb|lne_cb')
import sqlkit as sk
#from sqlkit.table import SqlWidgetTreeView
import gtk

from sqlalchemy import *

engine = sk.config.new_engine(echo=False, globalconn=True)


lay = """ {-
   user_id
   user_name
   user_last_name
#   user_birth_date
   user_address
#   city_id
   user_age
   user_sex
#   user_active
   A=uno - }
"""
   
zz = sk.SqlMask (table='euro_user', lay=lay, nick='user', single=True)
zz.w['Window'].hide()
z2 = sk.SqlTable(table='euro_mail', naked=True, addto=zz.w['A=uno'],nick='mail')
z2.lay_obj.prop('TV=tree', 'height-request', 150)
zz.w['Window'].show_all()

zz.sync_add(z2)
#zz.reload()


## Completion - you may choose how to show the completion list
## default is the first ending with _name or _descr
## NOTE: may also precede call to SqlMask

sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', None)

#dbg.gtk_dbg.ShowClassInfo(zz)
#print dir()
gtk.main()


