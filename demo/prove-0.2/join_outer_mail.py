#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import sqlkit as sk
#import dbg
#dbg.dbg = 1

from sqlalchemy import *
from layout import *

engine = sk.config.new_engine(echo=False, globalconn=True)
meta = default_metadata
session = create_session()

user_table = Table ('euro_user', engine, autoload=True)
mail_table = Table ('euro_mail', engine, autoload=True)

class User(object): pass
class Mail(object): pass
#user_mapper = mapper (User, user_table)
#mail_mapper = mapper (Mail, mail_table)

class Join(object): pass

join = user_table.outerjoin(
        mail_table,
        user_table.c.user_id == mail_table.c.mail_user_id
        )
m = Join.mapper = mapper(
    Join, join
    #, primary_key=[user_table.c.user_id]
#    Join, join
    )

engine.echo=True
ret = session.query(m).select()
M = sk.inspect.InspectMapper(m)
d = sk.sqldata.SqlData(ret, M)
d.printall()
sys.exit()







#sql_text = "user_id > :p"
sql_text = "mail_address ~* :mail_adsress"

engine.echo = True


params={'mail_address':'xo', 'user_name':'.'}


ret = m.select("user_name ~ :user_name AND mail_address ~ :mail_address",
                  params=params)
#ret = m.select(sql_text, from_obj=[mail_table], params={'p' : '5'}, limit=100)
i = 0
A = []
for R in ret:
    A += [R]
    i +=1
    print R.user_name, R.user_id, R.mail_address

sys.exit()
u = A[1]
u.city_pv = "RM"
u.user_name = "Grasso"
objectstore.commit()

