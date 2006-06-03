#!/usr/bin/env python

import sys

sys.path.append ('../../')
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg
import gtk

from sqlalchemy import *

engine = sk.config.spawnEngine(echo=False, globalconn=True)


lay = """
   user_name
   user_last_name
   user_birth_date
   user_address
   city_id
   user_age
   user_sex
   user_active
   H=uno -
"""
   
zz = sk.SqlMask (table='euro_user', lay=lay, nick='user')
z2 = SqlWidgetTreeView(table='euro_mail', naked=True, addto=zz.w['Huno'],
                       nick='mail')
z2.lay_obj.prop('TV=tree', 'height-request', 150)
# print sk.inspect.get_join_cnd([zz.fields.mapper.primarytable,
#                               z2.fields.mapper.primarytable], mode='str')
zz.sync_add(z2)
zz.reload()


## Completion - you may choose how to show the completion list
## default is the first ending with _name or _descr
## NOTE: may also precede call to SqlMask

sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', None)

#dbg.gtk_dbg.ShowClassInfo(zz)
#print dir()
gtk.main()


