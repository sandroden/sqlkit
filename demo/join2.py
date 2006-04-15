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

rm = relation(mm, lazy=False, backref='user')
rc = relation(mc, lazy=False)
User.mapper = mapper(User, tbusers, properties = {
    'city' : rc,
    'mails' : rm,
    })
z = User.mapper

#user = User()
#mail = Mail()
#city = City()

#eng.echo = True

#ret = User.mapper.select("user_name ~* '^S' ", order_by="mail_address")
ret = User.mapper.select("user_name ~* '^F' ")
info = reflect.InspectMapper(User.mapper)

### left outer join
#dd = sqldata.SqlData(ret,info, left=True)
dd = sqldata.SqlData(ret,info, left=False)
dd.fields(['user_name','pv','city','mail_address', 'user_age'])

#print dd
#print dd.index
#print dd.get()
for i in dd.pointers:
    #pass
    print i
dd.set({'user_age' : 16, 'city' : 'Roma'},index=0) 
#dd.set({'mail_address' : 'abc@uno.it'},index=0) 
#dd.set({'mail_address' : 'mio_mail@e-den.it'}, index=0)
dd.printall(mode='values')
# fat = ret[0]
merate = mc.select("city = 'Merate'")[0]
lecco = mc.select("city = 'Lecco'")[0]
print dd.show(merate)
print dd.show(lecco)

#print retc
#retc.pv = 'LE'
eng.echo = True
objectstore.commit()

# for i in range(len(dd.index)):
#     print dd.get(index=i,mode='')


