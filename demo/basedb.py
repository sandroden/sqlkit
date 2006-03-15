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
        self.eng = config.spawnEngine()
        self.tbusers = Table('euro_user', self.eng, autoload = True)
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
    print '--------------sel1'
    print sel1
    print '--------------sel2'
    print sel2

    rows1 = sel1.execute()
    rows2 = sel2.execute()
    print '--------------rows1'
    print rows1
    print '--------------rows2'
    print rows2

    print '--------------row1.fetchall()'
    rr = rows1.fetchall()
    for r in rr:
        print r['user_last_name']

    print '--------------row2.fetchall()'
    rr = rows2.fetchall()
    for r in rr:
        print r['user_last_name'],r.user_last_name

    print '--------------db.users.select_by(db.users.c.user_age>30)'
    userlist = db.users.select_by(db.users.c.user_age>30)
    for u in userlist:
        print u.user_id,u.user_last_name
        

    print "--------------db.users.select_by('user_age>30')"
    userlist = db.users.select_by('user_age>30')
    for u in userlist:
        print u.user_id,u.user_last_name
        

    print '--------------db.users.select(db.users.c.user_age>30)'
    userlist = db.users.select(db.users.c.user_age>30)
    for u in userlist:
        print u.user_id,u.user_last_name

    print '--------------db.users.select("user_age>30")'
    userlist = db.users.select('user_age>30')
    for u in userlist:
        print u.user_id,u.user_last_name
    
    #questo da un errore psycopg2    
    #print '--------------'
    #t=text("select * from euro_user where user_age>30",db.eng)
    #print t
    #userlist = db.users.select(text("select * from euro_user where user_age>30",db.eng))
    #for u in userlist:
        #print u.user_id,u.user_last_name

    