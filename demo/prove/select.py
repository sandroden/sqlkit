#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path

from sqlalchemy import *
import config
import reflect

eng = config.spawnEngine(echo=False)
users = Table('euro_user', eng, autoload = True)

eng.echo = True
#s = select([users.c.user_name])
#t = select(['user_name'], whereclause="euro_user ~* :euro_user", from_obj=['euro_user'], distinct=True, order_by=['user_name'], engine=eng)
#t = select(['user_name'], "euro_user ~* 's'", from_obj=['euro_user'], distinct=True, order_by=['user_name'], engine=eng)
#t = eng.text("SELECT DISTINCT user_name FROM euro_user WHERE user_name ~* :euro_user", params={'euro_user':'s'} )
t = eng.text("SELECT DISTINCT user_name FROM euro_user WHERE user_name ~* :euro_user")
ret = t.execute({'euro_user':'s'})
for i in ret:
    print i.user_name
#s = select([" DISTINCT user_name FROM euro_user WHERE user_name ~* 's'"] )
#s = eng.text(["SELECT DISTINCT user_name FROM euro_user WHERE user_name ~* :euro_user"], )
#s.execute(**{'euro_user' : 's'})
#print str(s)
#s.execute()

#s = select(['user_name'], "user_name ~* :user_name")
#s = select(['user_name'], "user_name ~* :user_name")
#str(s)
# ret = s.execute({'user_name':'s'})
# for i in ret:
#     print i.user_name
sys.exit()
