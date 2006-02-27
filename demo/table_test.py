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

        self.l.connect(
            ('tb=gtk-delete', 'clicked', self.deleteRow),
            ('tb=gtk-new',    'clicked', self.insertRow),
            ('tb=gtk-refresh',   'clicked', self.reload ),
            ('tb=gtk-quit',   'clicked', self.exit_now )
            )
        
        treeview = self.w['TV=tree']

        SqlTreeView.__init__(self, treeview, MappedClass,
                             checkClass=checkClass)
        

assign_mapper(User, users)


sqlt = MyLayout(User)

gtk.main()

