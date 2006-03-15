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

        self.users   = User()

    def commit(self):
        objectstore.commit()
        

if __name__ == '__main__':

    db = BaseDb()

    sel1 = db.tbusers.select(db.tbusers.c.user_age > 30)
    sel2 = db.tbusers.select('user_age > 30')
    print '--------------'
    print sel1
    print '--------------'
    print sel2

    rows1 = sel1.execute()
    rows2 = sel2.execute()
    print '--------------'
    print rows1
    print '--------------'
    print rows2

    rr = rows1.fetchall()
    for r in rr:
        print r['user_last_name']

    print '--------------'
    rr = rows2.fetchall()
    for r in rr:
        print r['user_last_name']

    print '--------------'
    userlist = db.users.select_by(db.users.c.user_age>30)
    for u in userlist:
        print u.c.user_id,u.c.user_last_name
        
    #print '--------------'
    #userlist = db.users.select_by('user_age>30')
    #for u in userlist:
        #print u.c.user_id,u.c.user_last_name
        
    #print '--------------'
    #userlist = db.users.select(db.users.c.user_age>30)
    #for u in userlist:
        #print u.c.user_id,u.c.user_last_name
