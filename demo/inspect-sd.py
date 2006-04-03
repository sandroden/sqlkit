#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path

from sqlalchemy import *
import config
import reflect

eng = config.spawnEngine()
tbusers = Table('euro_user', eng, autoload = True)
tbmail  = Table('euro_mail', eng, autoload = True)

class User(object):
    pass

class Mail(object):
    pass

rel = relation(mapper(Mail, tbmail))
User.mapper = mapper(User, tbusers, properties = {'addresses' : rel })
        
m = User.mapper

#userlist = m.select('user_age>30')

info = reflect.InspectMapper(m)
    
# for k,v in info.user_id.iteritems():
#     print k, v


for k in info:
    print k['name'], k['type'], k['col_spec']
    if k['pg_type'] is int:
        print "    -->> %s INTEGER" % k['name']
