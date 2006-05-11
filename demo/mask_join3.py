#!/usr/bin/env python

import sys
sys.path.append ('../../')
import sqlkit as sk
from sqlalchemy import *
#from layout import *
import gtk

engine = sk.config.spawnEngine(echo=False)
sk.SqlMask(tables=['euro_user', 'euro_mail', 'city'], 
           order_by=['city_pv','mail_address'], engine=engine)

gtk.main()
