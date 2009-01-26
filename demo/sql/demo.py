#!/usr/bin/env python
# -*- coding: utf-8 -*-   -*- mode: python -*-



import gtk
import sys
import os

pdir = os.path.dirname(os.getcwd())
ppdir = os.path.dirname(pdir)
sys.path.insert(0,pdir)    
sys.path.insert(0,ppdir)    

from sqlkit import debug as dbg
dbg.debug(True)
dbg.debug(True, gtk=True)
dbg.trace_class(ok='SqlTable|SqlWidget|SqlMask|Completion')
but = 'set_fkey_descr|(lookup|get)_value|[el]ne_cb|match_func' + \
    '|cell_.*_cb|lookup_value|is_fkey|instance2'
dbg.trace_function(exclude=but)

from demo_tour import Demo
import sqlkit
from sqlkit.widgets import SqlMask, SqlTable
from sqlkit.db import proxy, defaults, utils
import model

db = proxy.DbProxy(engine="sqlite:///model/movies.sqlite")

class DemoSql(Demo):
    def load_module(self, name):
        # set last_layout_object
        file_name = name + ".py"
        doc, body = self.readexample(file_name)

        ### fill text: src, notes, and xml
        self.insert_source(body, self.src)
        self.note.set_text(doc)

        ### exec the example
        GLOB = {
            'sqlkit': sqlkit,
            'SqlMask': SqlMask,
            'SqlTable': SqlTable,
            'gtk': gtk,
            'db': db,
            'model': model,

            }
        execfile(file_name, GLOB)
        self.last_lo = GLOB['t'].lay_obj
        self.last_w  = GLOB['t'].widgets
        self.t = GLOB['t']
        try:
            self.t1 = GLOB['t1']
        except:
            pass
            

        #self.xml.set_text(GLOB['l'].xml())
        self.create_widget_tree(toplevel=GLOB['t'].widgets['Window'])
        self.prepare_treestore_for_elements(GLOB['t'].lay_obj.elements)
        GLOB['t'].widgets['Window'].set_title(file_name)
        self.w['Window'].set_title("Esempio: %s" % (file_name))


d = DemoSql(xml=False, debug=True)

if len(sys.argv) > 1:
    d.load_module_by_idx(sys.argv[1])


gtk.main()

