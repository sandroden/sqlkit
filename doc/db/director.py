#!/usr/bin/python

import sys

import dbg
#dbg.debug(True)
dbg.debug(True, gtk=True)
dbg.trace_class(ok='SqlTable|SqlWidget|SqlMask|Completion')
but = 'set_fkey_descr|(lookup|set|get)_value|[el]ne_cb|match_func' + \
       '|cell_default_cb|cell_bool_cb'
dbg.trace_function(exclude=but)

import sqlkit
from sqlkit import SqlTable, SqlMask
from sqlkit.db import proxy, defaults, utils
import gtk


db = proxy.DbProxy(engine="sqlite:///movies.sqlite")
session = db.get_session()
utils.TableDescr('director', format='%(first_name).1s. %(last_name)s',
                 metadata=db.metadata)
utils.TableDescr('movie', format='%(title)s. %(year)s',
                 metadata=db.metadata)
def_director = defaults.Defaults('director', metadata=db.metadata)
def_director.set_defaults( {'last_name':'cognome...',})


def_movie = defaults.Defaults('movie', metadata=db.metadata)
#def_movie.fk( 'director_id', 'last_name', 'Olmi')

if 'm' in sys.argv:
    t2 = SqlMask(table='director', dbproxy=db, single=True,)
    
else:
    t2 = SqlTable(table='director', dbproxy=db, single=True, dev=False,
                  order_by='last_name',
                  rows=6,
                  #field_list='director_id,title'
                  )
#    t2.reload()
    
#    t2.totals.add_total('year')
#t2.mapper.local_table.metadata.bind.echo = True

#t2.completions.director_id.autostart=1
try:
    gtk.main()
except KeyboardInterrupt:
    pass



