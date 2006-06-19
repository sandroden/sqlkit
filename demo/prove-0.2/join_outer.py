#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import sqlkit as sk
import dbg.gtk_dbg

from sqlalchemy import *
from layout import *

engine = sk.config.new_engine(echo=False, globalconn=True)
session = create_session()

user_table = Table ('euro_user', engine, autoload=True)
city_table = Table ('city', engine, autoload=True)
mail_table = Table ('euro_mail', engine, autoload=True)

class User(object): pass
class City(object): pass
#user_mapper = mapper (User, user_table)
#mail_mapper = mapper (Mail, mail_table)

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
    Join, join2, primary_key=[user_table.c.city_id])

#sys.exit()

M = sk.inspect.InspectJoinMapper(m)

sql_text = "city_name ~* :city_name"

engine.echo = True
#params={'city_name':'o', 'user_name':'a'}
#ret = m.select("city_name ~ :city_name AND user_name ~ :user_name", params=params)

ret = session.query(m).select()
dd = sk.sqldata.SqlData(ret, M)
print dd.pointers
dd.printall()

for R in ret:
    print R.user_name, R.mail_address
sys.exit()
#ret = m.select(sql_text, from_obj=[mail_table], params={'p' : '5'}, limit=100)
i = 0
A = []
for R in ret:
    A += [R]
    i +=1
    print R.user_name, R.city_name, R.city_pv

gtk.main()
u = A[1]
u.city_pv = "RM"
u.user_name = "Grasso"
objectstore.commit()

gtk.main()
