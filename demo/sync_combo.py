#!/usr/bin/env python

import sys
sys.path.append ('../../')
import dbg
# if sys.platform.startswith('linux'):
#     dbg.conf_class_trace(ok='SqlTable|SqlMask')
#     dbg.debug(2)
#     lgm = dbg.ShowLogs(show=True)
#     lgm.conf(but='set_fkey_descr|lookup_value|set_value|ene_cb|lne_cb')
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
   
zz = sk.Combo(tables=['euro_user','euro_mail'], lay=lay, nick='user',
              field_list='mail_address, mail_info', single=True)

gtk.main()


