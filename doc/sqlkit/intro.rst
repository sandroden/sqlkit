.. _sqlkit:

sqlkit
=======


Sqlkit is a tool to edit __data__ in the easiest possible way, to be used in
building applications that use databases. It is not an editor tables shema: no
way to add columns or add foreig key relationships. 

A tipical usage can be::


  from sqlkit import SqlTable, SqlMask
  from sqlkit.db import proxy
  
  db = proxy.DbProxy(engine='sqledit:///db_authors')
  t2 = SqlMask(table='author', dbproxy=db, single=True)
     
that will pop up an editor for the record. Filter panel will be available
just clicking on the label of the fields.


sqlkit pre-conditions
---------------------

1. I suppose that you use PrimaryKeys and ForeignKeys throughout the db.
   If you don't use ForeignKeys sqlkit will just work w/o any special
   behaviour. If you don't use PrimaryKeys sqlkit will not even open the table.

2. I suppose you are using one single metadata. This is a limit but it's my
   normal environment. There's not really anything that cannot be changed
   easily about this, simply I didn't have need fo this, nor working cases.
   (While I was plenty of ideas on other features...)


.. 2. IMPORTANT: I suppose that if two columns have the same name, they
..    represent the same data. It may be father and sun of two different tables
..    when a ForeignKey is used, but in no way it will reference a different
..    object. This is limited to the data represented in the mask. Two tables
..    that will never be joined or referenced don't have this constraint.
	
..    Sqlkit uses this to easy writing values into GUI entries calling the
..    entries after their field_name.

..    This will happen also if we are not editing a join but just a single
..    table. Each time we finish editing a field (ie: 

..       - we move the focus to another entry in the mask, or 
..       - we try to save, or
..       - we accept a value from a completion entry) 

..     a select will retrieve the values from the secondary table 

2. A numerical Primary Key will not be shown (in normal mode, but dev=True
   change this behaviour).  If a ForeignKey constraint exists. In this case
   the lookup table will be parsed and the *first* char/text field will be
   used as descriptor.

   It is possible to overwrite this behaviour using
   ``sqlkit.db.utils``. More info in the :ref:`description`


sqlkit supported backend structure
----------------------------------

1. sqlkit is built on sqlalchemy that allows editing db with many
   different engines. I use it with postgres, mysql and sqlite. 
   Other engines are supported but need a very simple addition that I'd be
   willing to do on request.

2. SqlMask/SqlTable must accept a table or a mapper (a list of tables in the
   future, in that case a join will be done using cascade_mappers).

SqlMask
-------

   SqlMask is the main editing tool along with SqlTable.
   It creates a mapper on the fly if not provided and will use
   InspectMapper to know how to behave for each field. InspectMapper is 
   SqlMask.fields

   If no layout is provided it will be created on the fly.

   The layout is analized to understand wich fields are to be represented,
   in case a menubar and a toolbar are added.

   Fields will be shown in appropriate widgets:

     - gtk.Entry for Strings and numbers ( the latter are right aligned if
       they're not foreign keys)
     - dateedit.dateedit for dates and timestamp
     - gtk.Checkbox for bool
     - Entry with arrow (almost ComboBoxEntry) for ForeignKeys

   All fields will have a label that is sensible to mouse clicks. A mouse
   click pops up a filter widget
   
   All entries that represent fields or foreign keys are sensible to
   right-clik, ShiftEnter/Contro/Enter that allows the completion of the
   values to occur.


Completion
----------

   :ref:`completion` works well for entries in the mapper and for
   entries that point to a foreign table/fkey.
   
   The ListStore used for the completion is only filled on demand (right
   ShiftEnter/ControEnter) and the string already in the entry is used as
   whereclause condition, regexp/like are used as operator.

