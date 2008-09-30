#!/usr/bin/python 

import sys
import gtk
import dbg
dbg.debug(True, gtk=True)
dbg.trace_class(ok='SqlTable|SqlWidget|SqlMask|Completion')
but = 'set_fkey_descr|(lookup|get)_value|[el]ne_cb|match_func' + \
       '|cell_default_cb|cell_bool_cb|lookup_value|is_fkey|instance2'
dbg.trace_function(exclude=but)

from elixir_model import Director, Movie, Actor, Genre
#from elixir_model_autoload import Director, Movie, Actor, Genre

import sqlkit
import elixir
from sqlkit.db import proxy
from sqlkit import completion
from sqlkit.db.utils import TableDescr

#elixir.metadata.bind.echo = True

db = proxy.DbProxy(engine="sqlite:///movies.sqlite")
TableDescr('director', format="%(first_name)s %(last_name)s",
           metadata=db.metadata)

TableDescr('movie', format="%(title)s (%(year)s)",
           metadata=db.metadata)


lay = """
         title       year:5< 
         director_id - - 
         m2m=genres  - m2m=actors -
         """
tm = sqlkit.SqlMask(mapper=Movie.mapper, dbproxy=db , session=elixir.session,layout=lay)

#tm.completions.director_id.set_constraint(name__icontains='d')
tm.reload()

# tt = sqlkit.SqlTable(mapper=Movie.mapper, session=elixir.session)
# tt.reload()



# lay = """
#      name 
#      m2m=movies -
# """
# tm2 = sqlkit.SqlMask(mapper=Genre.mapper, metadata=__metadata__, session=elixir.session,layout=lay)
# t = tm.mfields['genres'].widget.table

gtk.main()
