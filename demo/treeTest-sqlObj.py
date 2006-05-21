#!/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path

from sqlalchemy import *
from layout import *
import sqlkit
from sqlkit.table import SqlObjTreeView
config = sqlkit.config
#import config
import dbg as sd
sd.dbg = 1
eng = config.spawnEngine()

eng.begin()
#eng.echo = 'debug'


users = Table('users', eng,
              Column('user_id', Integer, primary_key = True),
              Column('user_name', String(30), nullable = False),
              Column('user_last_name', String(30), nullable = False))

users.create()

users.insert().execute(
    {'user_name': 'Sam', 'user_last_name': 'Patts'},
    {'user_name': 'Sid', 'user_last_name': 'Watts'},
    {'user_name': 'Axe', 'user_last_name': 'Smith'},
    {'user_name': 'Ted', 'user_last_name': 'Will'})

mails = Table('mails', eng,
              Column('mail_address', String(30), nullable = True,
                     primary_key = True),
              Column('mail_user_id', Integer, ForeignKey("users.user_id")))

mails.create()

mails.insert().execute(
    {'mail_address': 'sam@example.com', 'mail_user_id': 1},
    {'mail_address': 'sid@example.com', 'mail_user_id': 2},
    {'mail_address': 'ted@example.com', 'mail_user_id': 4})
                       


res = join(users, mails).select().execute()

for r in res.fetchall():
    print r
    
class MappedTable(object):
    pass

j = join(users,mails)
#MappedTable.mapper = mapper(MappedTable, j)
assign_mapper(MappedTable, j)

m = MappedTable.mapper



for i in m.select():
    print i.user_id
    #i.user_id = i.user_id + 10

# aggiungo una riga
mT = MappedTable()
#mT.user_id = 5
mT.user_name = 'Fat'
mT.user_last_name = 'Joe'
mT.mail_address = 'fjoe@example.com'
mT.mail_user_id = mT.user_id

mT2 = MappedTable()
#mT2.user_id = 6
mT2.user_name = 'Jim'
mT2.user_last_name = 'Big'
mT2.mail_address = 'jbig@example.com'
mT2.mail_user_id = mT2.user_id

print dir(m.c.user_id), m.c.user_id.type
objectstore.commit()

class User(object):
    pass

class Mail(object):
    pass


mapMail = mapper(Mail, mails)

assign_mapper(User, users,
              properties = {'emails': relation(mapMail)})




        
users_mapper = User.mapper


class C(SqlObjTreeView):
    """Simple class extension to handle destroy event since we have only one window
    in this application."""
    def __init__(self, *args, **kwargs):
        """Overwrite init to connect delete_event from window
        to quit gtk main loop."""
        SqlObjTreeView.__init__(self, *args, **kwargs)
        self.treeview.get_toplevel().connect("delete_event", self.delete_event)


    def delete_event(self, w, e):
        """Pass event to parent object and quit the application."""
        SqlObjTreeView.delete_event(self, w, e)
        gtk.main_quit()
        return False

sqlt = C(users_mapper)
gtk.main()

eng.rollback()

