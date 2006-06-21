#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
import dbg
import layout
dbg.debug(True)
from planning import texviewer

#from sqlalchemy import *
import sqlalchemy as sa
import sqlkit as sk
import layout.misc
import gtk
engine = sk.config.new_engine(file='eurotex.ini', echo=False, globalconn=True)
session = sa.create_session()

class choice(object):
    def __init__(self, engine=engine, session=session):
        lay = " TVS=tree"
        self.tables = {}
        self.engine = engine
        self.session = session
        self.l = layout.Layout(lay)
        self.w = self.l.show()
        self.tv = self.w['TV=tree']
        cols = ['table', 'def', 'pkey', 'fkey']
        self.stv = layout.misc.EasyTreeView(cols, tv=self.tv)
        self.model = self.tv.get_model()
        #self.configure_treeview(self.tv)
        self.tv.connect('row-activated', self.activate_cb)
        self.fill_model()

    def activate_cb(self, tv, path, col):
        table = self.model.get_value(self.model.get_iter(path), 0)
        sk.SqlTable(table=table, session=self.session)

    def fill_model(self):
        tables = sk.inspect.list_tables(eng=engine)
        tables.sort()
        for table in tables:
            iter = self.model.append(None)
            self.model.set(iter, 0, table)
            tbl = sa.Table(table, self.engine, autoload=True)
            self.tables[table] = tbl
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
                
        
C = choice(engine=engine, session=session)


gtk.main()


