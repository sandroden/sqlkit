#!/usr/bin/python 

import sys
import gtk
#sys.path.insert(0, '../..')
import dbg
#dbg.debug(True, gtk=True)
dbg.trace_class(ok='SqlTable|SqlWidget|SqlMask|Completion')
but = 'set_fkey_descr|(lookup|get)_value|[el]ne_cb|match_func' + \
       '|cell_default_cb|cell_bool_cb|lookup_value|is_fkey|instance2'
dbg.trace_function(exclude=but)

#from elixir import *
import elixir
from datetime import datetime, timedelta

import time
import sqlkit 
from sqlkit.db import proxy
from sqlkit import completion

elixir.metadata.bind = "sqlite:///movies.sqlite"
#elixir.metadata.bind.echo = True

db = proxy.DbProxy(engine="sqlite:///movies.sqlite")
__metadata__ = db.metadata

class Director(elixir.Entity):
    last_name = elixir.Field(elixir.String(60))
    first_name = elixir.Field(elixir.String(60))
    movies = elixir.OneToMany('Movie', inverse='director', lazy="False")
    elixir.using_options(tablename='director')

    def __repr__(self):
        return u'<Director: %s>' %self.last_name

class Movie(elixir.Entity):
    title = elixir.Field(elixir.String(60))
    description = elixir.Field(elixir.String(512))
    year = elixir.Field(elixir.Integer())
    director = elixir.ManyToOne('Director', inverse='movies' , lazy="False")
    genres = elixir.ManyToMany('Genre', inverse='movies', tablename='movie_genre')   
    actors = elixir.ManyToMany('Actor', inverse='movies', tablename='movie_casting')
    elixir.using_options(tablename='movie')

    def __repr__(self):
        return u'<Movie: %s>' % self.title

class Genre(elixir.Entity):
    name = elixir.Field(elixir.Unicode(15), primary_key=True)
    movies = elixir.ManyToMany('Movie')
    elixir.using_options(tablename='genre')
#    elixir.using_options(session=ss)
    
    def __repr__(self):
        return u'<Genre "%s">' % self.name

class Actor(elixir.Entity):
    name = elixir.Field(elixir.String(60))
    elixir.using_options(tablename='actor')
    movies = elixir.ManyToMany('Movie', inverse='actors', tablename='movie_casting')

elixir.setup_all()

lay = """
         title       year:5< 
         director_id - - 
         m2m=genres  - m2m=actors -
         """
tm = sqlkit.SqlMask(mapper=Movie.mapper, metadata=__metadata__, session=elixir.session,layout=lay)

tt = sqlkit.SqlTable(mapper=Movie.mapper, metadata=__metadata__, session=elixir.session)

# lay = """
#      name 
#      m2m=movies -
# """
# tm2 = sqlkit.SqlMask(mapper=Genre.mapper, metadata=__metadata__, session=elixir.session,layout=lay)
# t = tm.mfields['genres'].widget.table
tm.reload()

completion.set_description_fields('director', 'last_name', add='first_name',
                      format="%(first_name)s %(last_name)s")

completion.set_description_fields('director', 'last_name', add='first_name',
                      format="%(last_name)s - (%(first_name)s)")

gtk.main()
