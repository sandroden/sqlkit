============
 Sqlwidget
============

This is the base class for :ref:`mask` and :ref:`table` that implements the
common interface.

main options
================


Any sqlwidget need a ``mapper`` and ``session``. It's possible to provide other
objects from which the sqlwidget infers them (eg.: the tablename and the
metadata where the table can be autoloaded, + the session)

Keep in mind that in order to make :ref:`relationships` to work you must
provide the mapper (possibly via the mapped class). The relations translate
PropertyLoaders (see sqlalchemy_ documentation) that do not belong to the table.

Metadata is also used when autoloading tables references by foreign keys to
display a better representation of the referenced record.

dbproxy
-------

Since a typical scenario is to have to provide a session different in each
SqlWidget and a metadata, an object is provided -``dbproxy``- that can be
initialized from the engine specification::

  from sqlkit import SqlMask, SqlTable, dbproxy
  db = proxy.DbProxy(engine="sqlite:///model/movies.sqlite")
  SqlTable(table="movies", dbproxy=db)

below you can see some alternatives that would work as well::

  Session = sessionmaker(bind=self.metadata.bind, autocommit=False)
  sess = Session()
  meta = MetaData()
  meta.bind = "sqlite:///model/movies.sqlite"
  #
  SqlTable(table="movies", session=sess, metadata=meta)

  # passing a mapped class (Movie here is build with declarative layer):
  # the metadata is found from the mapper.local_table.metadata

  SqlTable(Class=Movies, session=sess)


layout options
==============

:title:
   the title for the gtk.Window

:show:
   a boolean to tell if the Window will be visible

:dev:
   if a sqlwidget is opened in dev mode and no field_list is passed, the
   primary key is shown even if it's  a serial, if it's not in dev mode it
   will be hidden

:naked=False: 
   the table will be rendered without any buttons. It's used in layout when
   you want to add the table/mask to another layout (eg: in
   relationships). Default: False.

:addto=None:
   if set must be a container to which the sqlwidget will be added

mode/sql options
=================

:ro=False:
   if set to True the table is not updateable

:noup=[]:
   a list of field names that will not be allowed to update. The list may be
   also a string space or comma separated

:order_by=None:
   order by column to be used when selecting 

:limit=200:
   limit attribute to be used selectin

:field_list=None:
   a field_list to be shown. This can also be set via "set_fields". Operate
   via toggling visibility of the columns (is not a way to save bandwith at
   the moment)

:hide = None:
   field to be hidden (opposite to fiel_list)

:single=False:
   if a table is opened in single mode, destroying the table quits the gtk
   main loop.

Methods
=======

These methods are better explained elsewhere. I recap them here just for
completeness:

  :set_fields:
      equivalent to passing field_list

  :add_constraint:
      see :ref:`constraints`

  :add_filter:
      see :ref:`filters`

  :reload:
      reload the data from the database taking all filter/constraints into
      consideration 

Attributes
===========

:related: 
   a container for all related sqlwidgets

:completions:
   a container of all completion objects

.. :vfields:
..    a container for all validation fields. A validation fields is an objects
..    that lives in sqlkit.widgets.common.fields (temporary position) and that
..    knows how to represent a field and how to validate it. I'm thinking to
..    change it to fields,  but my mind is not made up...

:query:
   the sqlalchemy query object (``session.query(mapper)``) with all
   constraints applied. Can be manipulated as necessary as long as it stay a
   query object.

:lay_obj: 
   the sqlkit.layout.Layout object used to create the layout

:current:
   the object represented by a mask or a possible selected record in a
   table or None. 

:field_list:
   a list of the field names the GUI is handling. It comprises PropertyLoaders



.. _sqlalchemy: http://www.sqlalchemy.org

.. API
.. ===

.. .. automodule:: sqlkit.db.proxy
.. .. autoclass:: DbProxy
..    :members: get_session
  


Signals
=======

At the moment just one signal is defined. More will come up soon as I decide
which are the needed ones...

:record_selected:
   A record has been displayed in Mask or selected in Table.
   The callback will just receive the widget as argument.

