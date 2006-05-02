#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path, sd
import sqldata
import reflect

sd.dbg = 1

from sqlalchemy import *
import config
import reflect

eng = config.spawnEngine(echo=False)
tbusers = Table('euro_user', eng, autoload = True)
tbmail  = Table('euro_mail', eng, autoload = True)

class User(object):
    pass

class Mail(object):
    pass

m2 = mapper(Mail, tbmail)
#rel = relation(m2, lazy=False)
rel = relation(m2, lazy=True)
User.mapper = mapper(User, tbusers, properties = {'addresses' : rel })
        
m = User.mapper


info = reflect.InspectMapper(m)

#print info['mail_user_id']
#sys.exit()
# for k,v in info.user_id.iteritems():
#     print k, v


# for k in info:
#     print k['name'], k['type'], k['col_spec']
#     if k['pg_type'] is int:
#         print "    -->> %s INTEGER" % k['name']

#eng.echo = True
userlist = m.select('user_age > 10')

dd = sqldata.SqlData(userlist, info)
#dd.create_index(userlist, left=False)
dd.fields(fields=['user_name', 'mail_address'])
print dd.index
#print dd.next(mode='list')

z = userlist
zz = userlist[1]
# u.user_id = 100
# objectstore.commit()

for i in userlist:
    print i.user_name
    for a in i.addresses:
         print "     ", a.mail_address, a.mail_info
#         print i, a, i.user_name, a.mail_address, a.mail_info
#         #print i, a
#         #i.user_id += 100
#         a.mail_info = "%s - %s" % (i.user_name, a.mail_address.lower())

# objectstore.commit()

# for user in userlist:
#     for at in info.fields:
#         print at
#         print "    ", info.get(user, at)

        
