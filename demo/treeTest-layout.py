#!/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path

from sqlalchemy import *
from layout import *
import sqlkit
import dbg
import dbg.gtk_dbg
from sqlkit.table import SqlTreeView, SqlLayoutTreeView
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


import gtk
import gtk.glade


class MyLayout(SqlLayoutTreeView):

    def __init__(self, MappedClass, checkClass=None):
                ### The layout
        lay = """
          {B m=file m=modifica m=opzioni m=aiuto}
          {O tb=gtk-save tb=gtk-delete tb=gtk-new tb=gtk-refresh tb=gtk-quit}
          TVS=tree
        """
        self.l = Layout(lay,opts='s', title="ListStorageView")
        self.w = self.l.show(x=self.delete_event)
        self.window = self.w['Window']
        self.l.menu('m=file',
                    ('gtk-open', self.insertRow,),
                    ('-',None,),
                    ('gtk-quit', self.exit_now)
                    )

##         self.w['tb=gtk-delete'].connect('clicked', self.deleteRow)
##         self.w['tb=gtk-new'].connect('clicked', self.insertRow)
##         self.w['tb=gtk-quit'].connect('clicked', self.exit_now)

        self.l.connect(
            ('tb=gtk-delete', 'clicked', self.deleteRow),
            ('tb=gtk-new',    'clicked', self.insertRow),
            ('tb=gtk-refresh',   'clicked', self.reload ),
            ('tb=gtk-quit',   'clicked', self.exit_now )
            )
        

        # accel group  #### FIXME: dove viene usato?
        #accel_group = gtk.AccelGroup()
        #self.window.add_accel_group(accel_group)
        treeview = self.w['TV=tree']

        SqlTreeView.__init__(self, treeview, MappedClass,
                             checkClass=checkClass)
                
        
sqlt = MyLayout(User)
dbg.gtk_dbg.ShowClassInfo(sqlt)
gtk.main()

sys.exit()

for i in m.select():
    for c in m.columns.keys():
        print c, i.__getattribute__(c),
    print

for i in User.select():
    for c in User.c.keys():
        print c, i.__getattribute__(c),
    print
    
eng.rollback()

eng.begin()

eng.echo = 'debug'

users = Table('euro_user', eng, autoload = True)

mails = Table('euro_mail', eng, autoload = True)

class User(object):
    pass

class Mail(object):
    pass

mapMail = mapper(Mail, mails)

assign_mapper(User, users,
              properties = {'emails': relation(mapMail)})

        


sqlt = MyLayout(User)
gtk.main()

eng.commit()

