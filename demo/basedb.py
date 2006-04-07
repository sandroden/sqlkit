#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path

from sqlalchemy import *
import config

MODO = None


#class User(object):
    #pass

#class Mail(object):
    #def __init__(self, mail_address=None):
        #self.mail_address=mail_address
    #pass


class Utente(object):
    def __init__(self):       
        self.eng = config.spawnEngine()
        self.tbusers = Table('euro_user', self.eng, autoload = True)
        self.tbmail  = Table('euro_mail', self.eng, autoload = True)

        class User(object):
            pass

        class Mail(object):
            def __init__(self, mail_address=None):
                self.mail_address=mail_address
            pass

        if MODO == 'auto':
            assign_mapper(User, self.tbusers)
            assign_mapper(Mail, self.tbmail)
            cascade_mappers(User,Mail)
        else:
            User.mapper = mapper(User, self.tbusers, properties = {
                'mails' : relation(mapper(Mail, self.tbmail))
                })

        self.user = User()
        self.mail = Mail()
        
        
    def commit(self):
        objectstore.commit()
        

if __name__ == '__main__':

    ut = Utente()

    #sel1 = ut.tbusers.select(ut.tbusers.c.user_age > 30)
    #sel2 = ut.tbusers.select('user_age > 30')
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

    #print '--------------ut.users.select_by(ut.user.c.user_age>30) MODO =',MODO
    #if MODO == 'auto':
        #userlist = ut.user.select_by(ut.user.c.user_age>30)
    #else:
        #userlist = ut.user.mapper.select_by(ut.user.c.user_age>30)
    #for u in userlist:
        #print u.user_id,u.user_last_name
        

    #print "--------------ut.users.select_by('user_age>30') MODO = ",MODO
    #if MODO == 'auto':
        #userlist = ut.user.select('user_age>30')
    #else:    
        #userlist = ut.user.mapper.select_by('user_age>30')
    #for u in userlist:
        #print u.user_id,u.user_last_name
        

    #print '--------------ut.users.mapper.select("user_age>30"), con mapper esplicito- MODO =',MODO
    #userlist = ut.user.mapper.select('user_age>30')
    #for u in userlist:
        #print u.user_id,u.user_last_name
    
    #questo da un errore psycopg2    
    #print '--------------'
    #t=text("select * from euro_user where user_age>30",ut.eng)
    #print t
    #userlist = ut.user.select(text("select * from euro_user where user_age>30",ut.eng))
    #for u in userlist:
        #print u.user_id,u.user_last_name
        
        
    print '--------------INSERT - MODO =',MODO
    ut.user.user_last_name='Rossini'
    ut.user.user_name='Marco'
    ut.user.user_age=51
    ut.mail.mail_address = 'pluto@iol.it'
    ut.user.mails.append(ut.mail)
    ut.commit()


    #u = ut.user.mapper.select('user_last_name=Mancini')[0]
    #u.user_address = 'via marcora 10'
    #u.user_city    = 'Morbegno'
    #ut.commit()

    print '--------------JOIN - MODO =',MODO
    if MODO=='auto':
        userlist = ut.user.select('user_age>30')
        for u in userlist:
            for a in u.mails:
                print u.user_id,u.user_last_name,u.user_address,u.user_city,a.mail_address                
    else:    
        userlist = ut.user.mapper.select('user_age>30')
        for u in userlist:
            for a in u.mails:
                print u.user_id,u.user_last_name,u.user_address,u.user_city,a.mail_address
    
    
    
