#!/usr/bin/python

import sys

sys.path.insert(0, '../..')
import dbg
dbg.debug(True)
dbg.debug(True, gtk=True)
#dbg.trace_class(ok='SqlTable2|SqlWidget')
but = 'set_fkey_descr|(lookup|set|get)_value|[el]ne_cb|match_func' + \
       '|cell_default_cb|cell_bool_cb'
dbg.trace_function(exclude=but)

import sqlkit
from sqlkit import SqlTable, SqlMask
from sqlkit.db import proxy
import gtk


db = proxy.DbProxy(engine="sqlite:///movies.sqlite")
session = db.get_session()


t2 = SqlMask(table='movie', dbproxy=db, single=True,)
          


try:
    gtk.main()
except KeyboardInterrupt:
    pass



