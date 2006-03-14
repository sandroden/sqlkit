#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path

from sqlalchemy import *
import config


class BaseDb:
    def __init__(self):       
        eng = config.spawnEngine()
        self.tbusers = Table('euro_user', eng, autoload = True)

        class User(object):
            pass
        
        assign_mapper(User, self.tbusers)
        #userlist = User.select_by(user_age>20)

        self.users   = User()

    def commit(self):
        objectstore.commit()
        

if __name__ == '__main__':
    db = BaseDb()
    print '--------------'
    userlist = db.users.select_by(db.users.c.user_age>20)
    for u in userlist:
        print type(u.c['user_id']),type(u.c.user_id)
        print u.c['user_id'],u.c.user_last_name
    print '--------------'
    userlist = db.users.select_by('user_age>20')
    for u in userlist:
        print u.c.user_id,u.c.user_last_name
        
    print '--------------'
    userlist = db.users.select(db.users.c.user_age>20)
    for u in userlist:
        print u.c.user_id,u.c.user_last_name
