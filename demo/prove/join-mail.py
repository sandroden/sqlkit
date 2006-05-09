#!/usr/bin/env python

import sys ; sys.path.append ('../../../')
import sqlkit as sk
from sqlalchemy import *

engine = sk.config.spawnEngine(echo=False)
mail_table = Table ('euro_mail', engine, autoload=True)
user_table = Table ('euro_user', engine, autoload=True)

class User(object): pass
class Mail(object): pass

#user_mapper = mapper (User, user_table)
mail_mapper = mapper (Mail, mail_table)

rel = relation(mail_mapper, lazy=False )

m = mapper(User, user_table, properties = { 'mails' : rel } )
i = sk.inspect.InspectMapper(m)
#join = i.get_join_cnd()

#sql_text = "user_id > :p"
#sql_text = "mail_name ~* :p"

#sys.exit()
engine.echo = True
#ret = m.select_by("mail_name ~ 'o' AND user_name ~ 'a'")
#join =  i.get_join_cnd()
join =  [ user_table.c.user_id  == mail_table.c.mail_user_id ]
join += [ mail_table.c.mail_address.op('~')('a') ]


ret = m.select(
    user_table.c.user_id==mail_table.c.mail_user_id,
    mail_table.c.mail_address.like('%a%')
                )


# ret = m.select_by("mail_name ~ :b AND user_name ~ :b",
#                   params={'a':'o', 'b':'a'})

#ret = m.select(sql_text, from_obj=[mail_table], params={'p' : '5'}, limit=100)
for R in ret:
    print R.user_name, R.mails.mail_address

#engine.rollback()
