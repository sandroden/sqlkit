#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path

from sqlalchemy import *
from layout import *
from SqlTreeView import *
import config

import gtk
import gtk.glade


class Scheck(SqlChecker):
    """Sample checker class checking a primary key."""
    
    def rowInsertCheck(self, data):
        """Check if new value in first column is already in liststore."""

        print "INSERT Chek"
        pkeys = [x[0] for x in self.sqltreeview.dbrows]
        if int(data[0]) in pkeys:
            raise RowInsertError('Primary key not unique! Discarding data', data, 0)

    def rowUpdateCheck(self, old_data, data):
        """Check if new value in first column is already in liststore."""
        
        print "UPDATE Chek"
        pkeys = [x[0] for x in self.sqltreeview.dbrows]
        if int(data[0]) in pkeys and int(old_data[0])!=int(data[0]):
            raise RowUpdateError('Primary key not unique! Discarding data', data, 0)
        

eng = config.spawnEngine()
users = Table('euro_user', eng, autoload = True)
#mails = Table('euro_mail', eng, autoload = True)

eng = config.spawnEngine()

class User(object):
    pass

class Mail(object):
    pass


assign_mapper(User, users)
# assign_mapper(User, users,
#               properties = {'emails': relation(Mail, mails)})


sqlt = SqlLayoutTreeView(User)
gtk.main()

#eng.rollback()
