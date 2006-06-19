#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
import dbg
import layout
dbg.debug(True)
from planning import texviewer

from sqlalchemy import *
import sqlkit as sk
from layout import *

engine = sk.config.spawnEngine(file='eurotex.ini', echo=False, globalconn=True)
layout.map_labels(filename='label_map.txt')

lay = """
    a_codice
    a_note
    a_descr
    L=a_cn_trame_cm Toll=a_cn_trame_cm 
    LS=tex:400.300 -
"""
zz = sk.SqlMask(table='articolo', lay=lay)

tex = texviewer.TexViewer(zz.w['Lay=tex'])
class actions(sk.sqlwidget.Actions):
    def on_record_display(self, new):
        global tex
        dbg.write(tex, new['a_codice'])
        tex.cambia_articolo(new['a_codice'])
    

zz.actions = actions(zz)

gtk.main()


