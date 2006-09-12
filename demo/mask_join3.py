#!/usr/bin/env python

import sys
sys.path.append ('../../')
import sqlkit as sk
from sqlalchemy import *
#from layout import *
import gtk

engine = sk.config.new_engine(echo=False)

tables=['euro_user', 'euro_mail', 'city']
order_by=['city_pv','mail_address']

z = sk.SqlMask(tables=tables, order_by=order_by, engine=engine)
           

gtk.main()
