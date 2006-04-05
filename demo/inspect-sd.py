#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path, sd
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

rel = relation(mapper(Mail, tbmail))
User.mapper = mapper(User, tbusers, properties = {'addresses' : rel })
        
m = User.mapper


info = reflect.InspectMapper(m)
print info.keys()
sys.exit()
# for k,v in info.user_id.iteritems():
#     print k, v


# for k in info:
#     print k['name'], k['type'], k['col_spec']
#     if k['pg_type'] is int:
#         print "    -->> %s INTEGER" % k['name']

userlist = m.select('user_age > 30')

u = userlist[1]
print u.user_name
u.user_id = 100
objectstore.commit()

# for i in userlist:
#     print i.user_name
#     for a in i.addresses:
#         print i.user_name, a.mail_address, a.mail_info
#         #i.user_id += 100
#         a.mail_info = "%s - %s" % (i.user_name, a.mail_address.lower())

# objectstore.commit()

# for user in userlist:
#     for at in info.fields:
#         print at
#         print "    ", info.get(user, at)

        
