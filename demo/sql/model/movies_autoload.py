## DISCLAIMER: this file is not normally maintained

import os

from sqlalchemy.orm import declarative_base
from sqlalchemy import Table, Column, String, Date, Integer, Float, \
    Boolean, Numeric, ForeignKey, Unicode
from sqlalchemy.orm import relationship

from sqlkit.db.utils import Descr
from sqlkit.db import proxy
from model import engine

Base = declarative_base()
db = proxy.DbProxy(engine=engine, metadata=Base.metadata)

movie_casting = Table('movie_casting', Base.metadata, autoload_with=engine)
movie_genre = Table('movie_genre', Base.metadata, autoload_with=engine)

class Director(Base):
    __table__ = Table('director', Base.metadata, autoload_with=engine)

    def __repr__(self):
        return '<Director: %s (%s)>' % (self.last_name, self.nation)

class Movie(Base):
    __table__ = Table('movie', Base.metadata, autoload_with=engine)
    director = relationship('Director', backref='movies')
    genres = relationship('Genre', backref='movies', secondary=movie_genre)
    actors = relationship('Actor', backref='movies', secondary=movie_casting)

    def __repr__(self):
        return '<Movie: %s>' % self.title

class Genre(Base):
    __table__ = Table('genre', Base.metadata, autoload_with=engine)
#    name     = Column(Unicode(15), primary_key=True)

    def __repr__(self):
        return '<Genre "%s">' % self.name

class Actor(Base):
    __table__ = Table('actor', Base.metadata, autoload_with=engine)

    def __repr__(self):
        return '<Actor "%s">' % self.last_name

class Nation(Base):
    __table__ = Table('nation', Base.metadata, autoload_with=engine)
#     cod        = Column(String(4), primary_key=True)
#     nation     = Column(String(20))


class AllTypes(Base):
    __table = Table('all_types', Base.metadata, autoload_with=engine)
