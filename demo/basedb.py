#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path

from sqlalchemy import *
import config

MODO = None

class BaseDb:
    def __init__(self):       
        self.eng = config.spawnEngine()
        self.tbusers = Table('euro_user', self.eng, autoload = True)
        self.tbmail  = Table('euro_mail', self.eng, autoload = True)

        class User(object):
            pass

        class Mail(object):
            pass

        if MODO == 'auto':
            assign_mapper(User, self.tbusers)
            assign_mapper(Mail, self.tbmail)
            cascade_mappers(User,Mail)
        else:
            User.mapper = mapper(User, self.tbusers, properties = {
                'addresses' : relation(mapper(Mail, self.tbmail))
                })
        

        self.user = User()
        self.mail = Mail()
        

    def commit(self):
        objectstore.commit()
        

if __name__ == '__main__':

    db = BaseDb()

    #sel1 = db.tbusers.select(db.tbusers.c.user_age > 30)
    #sel2 = db.tbusers.select('user_age > 30')
    #print '--------------sel1'
    #print sel1
    #print '--------------sel2'
    #print sel2

    #rows1 = sel1.execute()
    #rows2 = sel2.execute()
    #print '--------------rows1'
    #print rows1
    #print '--------------rows2'
    #print rows2

    #print '--------------row1.fetchall()'
    #rr = rows1.fetchall()
    #for r in rr:
        #print r['user_last_name']

    #print '--------------row2.fetchall()'
    #rr = rows2.fetchall()
    #for r in rr:
        #print r['user_last_name'],r.user_last_name

    print '--------------db.users.select_by(db.user.c.user_age>30) MODO =',MODO
    if MODO == 'auto':
        userlist = db.user.select_by(db.user.c.user_age>30)
    else:
        userlist = db.user.mapper.select_by(db.user.c.user_age>30)
    for u in userlist:
        print u.user_id,u.user_last_name
        

    #print "--------------db.users.select_by('user_age>30') MODO = ",MODO
    #if MODO == 'auto':
        #userlist = db.user.select('user_age>30')
    #else:    
        #userlist = db.user.mapper.select_by('user_age>30')
    #for u in userlist:
        #print u.user_id,u.user_last_name
        

    #print '--------------db.users.mapper.select("user_age>30"), con mapper esplicito- MODO =',MODO
    #userlist = db.user.mapper.select('user_age>30')
    #for u in userlist:
        #print u.user_id,u.user_last_name
    
    #questo da un errore psycopg2    
    #print '--------------'
    #t=text("select * from euro_user where user_age>30",db.eng)
    #print t
    #userlist = db.user.select(text("select * from euro_user where user_age>30",db.eng))
    #for u in userlist:
        #print u.user_id,u.user_last_name

    print '--------------JOIN - MODO =',MODO
    if MODO=='auto':
        userlist = db.user.select('user_age>30')
        for u in userlist:
            for a in u.mails:
                print u.user_id,u.user_last_name,a.mail_address                
    else:    
        userlist = db.user.mapper.select('user_age>30')
        for u in userlist:
            for a in u.addresses:
                print u.user_id,u.user_last_name,a.mail_address
    