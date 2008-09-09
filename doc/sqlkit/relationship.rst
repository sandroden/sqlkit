
================
Relationship
================

Sqlkit makes editing of data that have relation as one2many of many2many
very simple. It's as easy as adding a field in the layout of the SqlMask.

One2Many in a SqlMak
=====================

This is a very powerfull feature of ``sqlkit`` that is built on top of
``sqlalchemy``'s mechanism of properties and session and on the ability of
``layout`` to let you define in a simbolic way a widget.

In the following example we will use a ``Mask`` to represent Directors 
and a ``Table`` to represent films, connected to the first by a OneToMany
relationship.

Suppose you already define a couple of tables in sqlalchemy, we will do it
using elixir_ that slightly simplyfies the syntax::

  class Director(elixir.Entity):
      last_name = elixir.Field(elixir.String(60))
      first_name = elixir.Field(elixir.String(60))
      movies = elixir.OneToMany('Movie', inverse='director', )
      elixir.using_options(tablename='director')
  
      def __repr__(self):
          return u'<Director: %s>' %self.last_name
  
  class Movie(elixir.Entity):
      title = elixir.Field(elixir.String(60))
      year = elixir.Field(elixir.Integer())
      director = elixir.ManyToOne('Director', inverse='movies' )
      elixir.using_options(tablename='movie')
  
      def __repr__(self):
          return u'<Movie: %s>' % self.title
  
To get a mask that:
 
 1. lets you see director and films toghether
 2. lets you edit them adding adn deleting at will

You just have to start te SqlMask like this:

  lay = """first_name last_name
         o2m=movies      - - -
         """
  SqlMask(mapper=Director.mapper, metadata=__metadata__, 
          session=elixir.session,layout=lay)


Ad you will get a mask that looks like this:

.. image:: ../img/director_movies.png


delete behaviour
----------------

We leave to sqlalchemy the responsability to decide if a film must be
deleted from the database or must just updated to set the director_id to NULL.
To change this behaviour you must act on the cascade property of the
relation (or directly on the database definition). If yo want to delete a
film in stead of just setting the property to NULL you can define the table
in this way::

  
  class Director(elixir.Entity):
      ...
      movies = elixir.OneToMany('Movie', inverse='director', 
               cascade="all, delete-orphan" ### note this line
		      )		
      ...
  

.. _elixir: http://elixir.ematia.de

limitation
-----------


The current version does not allows to filter on the fields of a related
table.

Many2many relationship
=========================

many2many relationship are as easy as one2many. Once again sqlalchemy
does the heavy job. Definition is as simple as::


    lay = """year title
             m2o=genres - - -
             """
    tm = sqlkit.SqlMask(mapper=Movie.mapper, metadata=__metadata__, 
                        session=elixir.session,layout=lay)
    lay = """
         name 
         m2m=movies -
    """
    tm2 = sqlkit.SqlMask(mapper=Genre.mapper, metadata=__metadata__, 
                         session=elixir.session,layout=lay)
      

and will pop up a couple of windows as the following, showing the same data
from the two different main tables: movies with theis genres and genres with
they're movies.

.. image:: ../img/m2m.png

  

