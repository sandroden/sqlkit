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



eng = config.spawnEngine()
users = Table('euro_user', eng, autoload = True)
#mails = Table('euro_mail', eng, autoload = True)

eng = config.spawnEngine()

class User(object):
    pass

class Mail(object):
    pass


assign_mapper(User, users)


sqlt = SqlLayoutTreeView(User)
gtk.main()

