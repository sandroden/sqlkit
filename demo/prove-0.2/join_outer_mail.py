
#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import sqlkit as sk
#import dbg
#dbg.dbg = 1

from sqlalchemy import *
from layout import *

engine = sk.config.new_engine(echo=False, globalconn=True)
#engine = create_engine('postgres://sandro:vicie@localhost:5433/test')
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
        ).select()
print str(join)
#print str(mail_table.select(mail_table.c.mail_address))
print join.select([join.c.user_name, join.c.mail_address], from_obj=[join])

sys.exit()

m = Join.mapper = mapper(
    Join, join
    #, primary_key=[user_table.c.user_id]
#    Join, join
    )

#engine.echo=True
ret = session.query(m).select('user_id = 5')
M = sk.inspect.InspectMapper(m)
d = sk.sqldata.SqlData(ret, M, session)
#d.printall(mode='dict')
d.printall()
R = ret[0]
sys.exit()



