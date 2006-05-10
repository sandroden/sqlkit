#!/usr/bin/env python

import sys
sys.path.append ('../../')
import sqlkit as sk
from sqlalchemy import *
#from layout import *
import gtk

engine = sk.config.spawnEngine(echo=False)
user_table = Table ('euro_user', engine, autoload=True)
city_table = Table ('city', engine, autoload=True)
mail_table = Table ('euro_mail', engine, autoload=True)

class Join(object): pass

join = user_table.outerjoin(
        city_table,
        user_table.c.city_id == city_table.c.city_id
        )

join2 = join.outerjoin(
        mail_table,
        mail_table.c.mail_user_id == user_table.c.user_id
        
)

m = Join.mapper = mapper(
    Join, join2)
#    , primary_key=[user_table.c.city_id])

#sys.exit()
sk.SqlMask(mapper=m, order_by=['city_pv','mail_address'])

gtk.main()
