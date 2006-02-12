#!/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path

from sqlalchemy import *
from layout import *
from SqlTreeView import *
import reflect

eng = create_engine('postgres', 
                    {'database':'test', 
                     'user':'test', 
                     })

user = reflect.mapTable(engine,'euro_user')
mail = reflect.mapTable(engine,'euro_mail')
res = join(user, mail).select().execute()

for r in res.fetchall():
    print r
    
class MappedTable(object):
    pass

j = join(user, mail)
#MappedTable.mapper = mapper(MappedTable, j)
assign_mapper(MappedTable, j)

m = MappedTable.mapper

for i in m.select():
    print i.user_id
    #i.user_id = i.user_id + 10

class User(object):
    pass

class Mail(object):
    pass


assign_mapper(User, users,
              properties = {'emails': relation(Mail, mails)})


import gtk
import gtk.glade


class Scheck(SqlChecker):
    """Sample checker class checking a primary key."""
    
    def rowInsertCheck(self, data):
        """Check if new value in first column is already in liststore."""

        pkeys = [x[0] for x in self.sqltreeview.dbrows]
        if int(data[0]) in pkeys:
            raise RowInsertError('Primary key not unique! Discarding data', data, 0)

    def rowUpdateCheck(self, old_data, data):
        """Check if new value in first column is already in liststore."""
        
        pkeys = [x[0] for x in self.sqltreeview.dbrows]
        if int(data[0]) in pkeys and int(old_data[0])!=int(data[0]):
            raise RowUpdateError('Primary key not unique! Discarding data', data, 0)
        
sqlt = SqlLayoutTreeView(User)
gtk.main()



