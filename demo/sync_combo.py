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
import gtk

from sqlalchemy import *

engine = sk.config.new_engine(echo=False, globalconn=True)


lay = """ {-
   user_id
   user_name
   user_last_name
   user_address
   user_age
   user_sex
   A=table - }
"""
   
class  act(sk.sqlwidget.Actions):
    def on_filter_reload(self, R):
        print "user_name: %s ",R['user_name']
        zz.reload(("user_name = :user_name", {'user_name': R['user_name']})) 

actions = act()

zz = sk.Combo(tables=['euro_user','euro_mail'],
              lay=lay,
              nick='user',
              filter=['user_name', 'mail_address'],
              field_list='mail_address, mail_info',
              actions=actions,
              geom=(500,700),
              single=True)

user_table = Table ('euro_user', engine, autoload=True)
mail_table = Table ('euro_mail', engine, autoload=True)

zz.filter_panel.set_reload(join=join(user_table, mail_table))

gtk.main()


