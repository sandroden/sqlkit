#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import sys, re, datetime
sys.path.append ('../../')
import dbg 
dbg.conf_class_trace(ok='SqlTable|Completion')

from sqlalchemy import *
import sqlkit as sk
import gtk
dbg.debug(True)
#dbg.debug(False)
import sqlalchemy
#import sqlalchemy.mods
#import sqlalchemy.mods.threadlocal
#from flogger import *

eng = sk.config.new_engine(globalconn=True)
meta = default_metadata
session = create_session()
dbg.write(session)
#eng = create_engine('postgres://test:vicie@localhost:5433/test')

#meta =  BoundMetaData(eng)

#table='euro_user'
table='euro_mail'
#table='jobs'
fields='user_id, user_name, user_last_name, user_sex, user_birth_date, user_age'
fields=None

lgm = dbg.ShowLogs(show=True)
lgm.conf(but='lookup_value|set_fkey_descr')
#lgm.log(sk.SqlTable)


# class act(sk.sqlwidget.Actions):
#     def on_completion(self, new, field_name):
#         if field_name == 'mail_user_id':
#             #SQL= "AND filo.f_titolo = :f_titolo AND filo.ft_id = :ft_id"
#             SQL = "AND mail_address ~ :mail_addr"
#             params = {'mail_addr' : '[2y]'}
#             return (SQL, params)

zz = sqlt = sk.SqlTable(table=table, session=session, field_list=fields,
                        single=True, dev=True, nick='tree', )
#zz.actions = act(zz)

# , noup=['user_age']
#zz.w['Window'].set_geometry_hints(None, base_width=300, base_height=200)
zz.w['Window'].set_geometry_hints(None, min_width=400, min_height=600)


#zz.order_by = 'user_address'
#zz.treeview.set_rules_hint(True)

#lgm.log(zz)
#lgm.log(zz.completion, but='_lookup_value')

#eng.echo = True
gtk.main()


