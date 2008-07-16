#!/usr/bin/python 

import sys

sys.path.insert(0, '../..')
import dbg
dbg.debug(False)
dbg.debug(True, gtk=True)
#dbg.trace_class(ok='SqlTable|SqlWidget|SqlMask')
but = 'set_fkey_descr|(lookup|set|get)_value|[el]ne_cb|match_func' + \
       '|cell_default_cb|cell_bool_cb|lookup_value'
dbg.trace_function(exclude=but)

from elixir import *

metadata.bind = "sqlite:///movies.sqlite"
#metadata.bind.echo = True

from datetime import datetime, timedelta

import time
import sqlkit 
from sqlkit.db import proxy
import gtk
db = proxy.DbProxy(engine="sqlite:///movies.sqlite")

def get_session(obj):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=metadata.bind)
    return Session.object_session(obj)

class Director(Entity):
    last_name = Field(String(60))
    first_name = Field(String(60))
    movies = OneToMany('Movie', inverse='director')
    using_options(tablename='director')

    def __repr__(self):
        return u'<Director: %s>' %self.last_name

class Movie(Entity):
    #id = Field(Integer, primary_key=True)
    title = Field(String(60))
    description = Field(String(512))
    date_release = Field(DateTime)
    director = ManyToOne('Director', inverse='movies')
    actors = ManyToMany('Actor', inverse='movies', tablename='movie_casting')
    genres = ManyToMany('Genre', inverse='movies', tablename='movie_genre')   
    using_options(tablename='movie')

    def __repr__(self):
        return u'<Movie: %s>' % self.title

class Genre(Entity):
    name = Field(Unicode(15), primary_key=True)
    movies = ManyToMany('Movie')
    using_options(tablename='genre')
    
    def __repr__(self):
        return u'<Genre "%s">' % self.name

class Actor(Entity):
    name = Field(String(60))
    movies = ManyToMany('Movie', inverse='actors', tablename='movie_casting')
    using_options(tablename='actor')

setup_all()

olmi = Director.get_by(last_name='Olmi', first_name='Ermanno')
f100 = Movie.get_by(title='100 chiodi')
#re = Movie(title='La leggenda del re pescatore')
#pirati = Movie(title='Cantando dietro il paraventi')
#olmi.movies=[f100, re, pirati]
#olmi.movies.append(re)
#olmi.movies.append(pirati)


#create_all()

#session.flush()

t1 = sqlkit.SqlMask(mapper=Movie.mapper, metadata=metadata, session=session,)
#t1.reload()
#t2 = sqlkit.SqlTable(mapper=Director.mapper, metadata=metadata, session=session)

#print f100.director
#print t1.records
#print t1.records[0].director

# for j in t1.session:
#     print j, get_session(j)
#     print j.director

#q = session.query(Movie)
#r2 = q.filter_by(director_id=1).all()

gtk.main()
