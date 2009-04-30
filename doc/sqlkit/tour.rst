======================= 
Sqlkit feature's tour
=======================

.. _sqlkit:

Features
========


Sqlkit is a tool to edit __data__ in the easiest possible way, to be used
building applications that use databases. It is not an editor for tables
schemas: no way to add columns or add foreign key relationships is provided.

A typical usage can be::


  from sqlkit.widgets import SqlTable, SqlMask
  from sqlkit import DbProxy
  
  db = DbProxy(engine='sqledit:///movies.sqlite')
  t = SqlMask(table='movie', dbproxy=db, single=True)
     
that will pop up an editor for the record. Filter panel will be available
just clicking on the label of the fields.



Main features of sqlkit:

 - editor of databases in 2 modes: :ref:`table` & :ref:`mask`
 - based on sqlalchemy_: can cope with many different databases
 - very powerfull :ref:`filtering <filters>` capabilities:

   * each field can be used to filter visible records
   * date filtering possible also on relative basis (good for saved
     queries)
   * works on expressions too

 - :ref:`completion` both on normal fields and foreign key fields
 - very easy way to draw a layout for mask views
 - :ref:`sqledit`: python script to edit db
 - completely effortless editing of :ref:`relationships`
 - very easy way to set :ref:`defaults`
 - possibility to display :ref:`totals` in numeric fields
 - :ref:`constraints`: any possible sql constraint can be attached to a Mask 
   or a Table. It can be expressed as a normal sqlalchemy query or with
   django-like syntax. Works on expressions too.
 - :ref:`signals`
 - :ref:`hooks` for a very easy customization of behaviour and for validation
 - more than 50 snippets of code to test each feature

.. _sqlalchemy: http://www.sqlalchemy.org

Views
-----

Two possible views: table & mask

.. image:: ../img/viste.png

that where requested by the following instructions::

   layout = """
       nome cognome 
       lato legame

     {|>.partecipanti
       n_adulti:10 n_bambini          l=uno c=uni
       n_adulti_ok n_bambini_ok    l=due c=due
       } - - -

      letto inviata
     cena canti 
     """
   t1 = SqlMask(table='partecipazioni_invitato', dbproxy=db, 
             hide='email note', layout=layout, )
   t2 = SqlTable(table='partecipazioni_invitato', dbproxy=db, )

Filter
------


Each label of both views can be clicked to get a filter panel:
   
.. image:: ../img/filter-panel.png

Completion
----------

:ref:`completion` is triggered by F1 key, Ctrl-Enter or Shift-Enter.  If the
field is a foreign key it will pop up a list of foreign values otherwise it
will show values currently used (just for varchar fields). 

The search for completion is done using the (possibly) already written
letters as filter: Control will match them at the beginning of the field,
Shift (and F1) will match them in any part. The search is made using
``LIKE`` operators or ``regexp`` according to whatever is available in the
db engine in use.


Layout
------

Very easy way to draw a layout. See :ref:`layout` widgets for a tour.


Sqledit
-------

A full featured program (python script) that can browse a database. Many
options (``sqledit -h``).

..  image:: ../img/sqledit.png

Just try it out on your preferred database using the url in a form as one
of the examples::

  sqledit postgres://localhost/mydb
  sqledit postgres://sandro:passwd@host:5444/mydb
  sqledit mysql://localhost/mydb
  sqledit sqlite:///movies.sqlite


the last is a very minimal db present in ``doc/db/movies.sqlite``

Relationships
-------------

:many2one: are just recognized automatically with simple introspection
:many2many: is very simply added to SqlMask declaring in the layout and
            attribute with that name
:one2many:  same as many2many

Many more detail in :ref:`relationships`

Totals
------

It's possible to display totals and subtotals in a table view. More in 
:ref:`totals`

Constraints
-----------

A :ref:`contraint <constraints>` can be as simple as::

  t = SqlTable(table='movie', dbproxy=db)
  t.add_constraints(actors__country='ITA', genres__name='drama',
    year__gte=1950, year__lte=1970)

And browsing of movies will be constrained into dramas with at least one
italian actor, produced between 1950 and 1970. The double underscore '__'
will allow spanning from one table to a related (provided a relation was
established at sqlalchemy level) and from attribute name to operator to e
used.  


Basic assumptions
=================

1. You use PrimaryKeys and ForeignKeys throughout the db.
   If you don't use ForeignKeys sqlkit will just work w/o any special
   behaviour. If you don't use PrimaryKeys sqlkit will not even open the table.

2. You are using one single metadata. This is a limit but it's my normal
   environment. There's not really anything that cannot be changed easily
   about this, simply I didn't have need for this, nor working cases.  (While
   I was plenty of ideas on other features...)

.. _fkey:

ForeignKeys
===========

Everywhere there's a ForeignKey I try to represent it in
the best possible way. More info in the completion chapter:
:ref:`description`


sqlkit supported backend structure
==================================

1. sqlkit is built on sqlalchemy that allows editing db with many
   `different engines`_. I use it with postgres, mysql and sqlite. 
   Other engines are supported but need a very simple addition that I'd be
   willing to do on demand.

2. SqlMask/SqlTable must be fed with a table, a class (eg: from declarative
   layer) or a mapper.

.. _`different engines`: http://www.sqlalchemy.org/trac/wiki/DatabaseNotes
