#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
import dbg
import layout
dbg.debug(True)
from planning import texviewer

from sqlalchemy import *
import sqlkit as sk
import layout.misc
import gtk
engine = sk.config.spawnEngine(file='eurotex.ini', echo=False, globalconn=True)

class choice(object):
    def __init__(self, engine=engine):
        lay = " TVS=tree"
        self.engine = engine
        self.l = layout.Layout(lay)
        self.w = self.l.show()
        self.tv = self.w['TV=tree']
        cols = ['table', 'def', 'pkey', 'fkey']
        self.stv = layout.misc.EasyTreeView(cols, tv=self.tv)
        self.model = self.tv.get_model()
        #self.configure_treeview(self.tv)
        self.tv.connect('row-activated', self.activate_cb)
        self.fill_model()


#     def configure_treeview(self, tv):
#         self.model = gtk.TreeStore(str, str, str, str)
        
#         for i,col in enumerate(cols):
#             self.tvc[i] = gtk.TreeViewColumn(col, gtk.CellRendererText(), text=i)
#             self.tvc[i].set_sort_column_id(i)
#             self.tv.append_column(self.tvc[i])

#         col = gtk.TreeViewColumn('table', gtk.CellRendererText(), text=0)
#         tv.append_column(col)
#         self.fill_model()
#         tv.set_model(self.model)
#         tv.connect('row-activated', self.activate_cb)

    def activate_cb(self, tv, path, col):
        table = self.model.get_value(self.model.get_iter(path), 0)
        sk.SqlTable(table=table)

    def fill_model(self):
        tables = sk.inspect.list_tables(eng=engine)
        tables.sort()
        for table in tables:
            iter = self.model.append(None)
            self.model.set(iter, 0, table)
            tbl = Table(table, self.engine, autoload=True)
            pks = []
            for pk in tbl.primary_key:
                pks += [pk.name]
            self.model.set(iter, 2, ",".join(pks))
            
            for c in tbl.c:
                col = self.model.append(iter)
                self.model.set(col, 0, c.name )
                self.model.set(col, 1, c.type.get_col_spec())
                if c.primary_key:
                    self.model.set(col, 2, 'X' )
                if c.foreign_key:
                    self.model.set(col, 3, repr(c.foreign_key) )
                
        
choice(engine=engine)


gtk.main()


