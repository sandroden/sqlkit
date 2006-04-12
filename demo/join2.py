#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path, sd

from sqlalchemy import *
import config
import reflect, sqldata
sd.dbg = 1

class User(object):
    pass

class City(object):
    pass

class Mail(object):
    pass

eng = config.spawnEngine()
tbusers = Table('euro_user', eng, autoload = True)
tbmail  = Table('euro_mail', eng, autoload = True)
city    = Table('city', eng, autoload = True)
mm = mapper(Mail, tbmail)
mc = mapper(City, city)

rm = relation(mm, lazy=False)
rc = relation(mc, lazy=False)
User.mapper = mapper(User, tbusers, properties = {
    'city' : rc,
    'mails' : rm,
    })
z = User.mapper
user = User()
mail = Mail()
city = City()

eng.echo = True
ret = user.mapper.select(order_by="mail_address")
info = reflect.InspectMapper(User.mapper)
### left outer join
#dd = sqldata.SqlData(ret,info, left=True)
dd = sqldata.SqlData(ret,info, left=False)
dd.fields(['user_name','pv','city','mail_address', 'user_age'])
#print dd
#print dd.index
#print dd.get()
for i in range(len(dd.index)):
    print dd.get(index=i,mode='')


