#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

import sys, re, datetime

sys.path.append ('../../../')
#sys.path.append ('../../')
import py_path

from sqlalchemy import *
import config

MODO = None


class User(object):
    pass

class Mail(object):
    def __init__(self, mail_address=None):
        self.mail_address=mail_address

class Utente(object):
    def __init__(self):       
        self.eng = config.spawnEngine()
        self.tbusers = Table('euro_user', self.eng, autoload = True)
        self.tbmail  = Table('euro_mail', self.eng, autoload = True)

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

    U = Utente()
    ut = User()

        
    ut.user_last_name='Rossini'
    ut.user_name='Marco'
    ut.user_age=51
    ut.user_id=111

    ut.mail.mail_address = 'pluto@iol.it'
    ut.user.mails.append(ut.mail)
    U.eng.echo = True
    objectstore.commit()
    sys.exit()

    print '--------------JOIN - MODO =',MODO
    if MODO=='auto':
        userlist = U.select('user_age>30')
        for u in userlist:
            for a in u.mails:
                print u.user_id,u.user_last_name,u.user_address,u.user_city,a.mail_address                
    else:    
        userlist = U.mapper.select('user_age>30')
        for u in userlist:
            for a in u.mails:
                print u.user_id,u.user_last_name,u.user_address,u.user_city,a.mail_address
    
    
    
