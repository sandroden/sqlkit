.. _sqlkit:

=======
sqlkit
=======


Sqlkit is a tool to edit __data__ in the easiest possible way, to be used in
building applications that use databases. It is not an editor of tables: no
way to add columns or add foreig key relationships. 

A tipical usage can be::


  from sqlkit import SqlTable, SqlMask
  from sqlkit.db import proxy
  
  db = proxy.DbProxy(engine='sqledit:///db_authors')
  t2 = SqlMask(table='author', dbproxy=db, single=True)
     
that will pop up an editor for the record. Filter panel will be available
just clicking on the label of the fields.


.. sidebar:: Naming convention

  Some advantages are only reached using a structure for the db that helps
  sqlkit understand what to do. This can be considered a limit but is what can
  speed up propgramming a lot. Below I try to summarize the assumptions made on
  the db. 
  

special endings for field_name are:

  :_id:    the column is a numeric id (sometime substitued with a description)
  :_key:   the column is a varchar code
  :_name \| _descr: 
           the column is a description for the record and will be
           used when showing the values instead of the _id. 

sqlkit pre-conditions
======================

1. I suppose that you use PrimaryKeys and ForeignKeys throughout the db.
   If you don't use ForeignKeys sqlkit will just work w/o any special
   behaviour. If you don't use PrimaryKeys sqlkit will not be able to update.

2. IMPORTANT: I suppose that if two columns have the same name, they
   represent the same data. It may be father and sun of two different tables
   when a ForeignKey is used, but in no way it will reference a different
   object. This is limited to the data represented in the mask. Two tables
   that will never be joined or referenced don't have this constraint.
	
   Sqlkit uses this to easy writing values into GUI entries calling the
   entries after their field_name.

   This will happen also if we are not editing a join but just a single
   table. Each time we finish editing a field (ie: 

      - we move the focus to another entry in the mask, or 
      - we try to save, or
      - we accept a value from a completion entry) 

    a select will retrieve the values from the secondary table 

3. A numerical Primary Key will not be shown (in normal mode, but dev=True
   change this behaviour).  If a foreignKey constraint exists. In this case
   the lookup table will be parsed and the *first* field name terminating
   with _name or _descr will be used as descriptor.

   It is possible to overwrite this behaviour using
   sqlkit.completion.set_description_field 


sqlkit data structure
======================

1. sqlkit/sqlmask is built on sqlalchemy that allows editing db with many
   different engines

2. SqlMask/SqlTable must accept a table or a mapper (a list of tables in the
   future, in that case a join will be done using cascade_mappers).

SqlMask
=========


    SqlMask is the main editing tool along with SqlTable.
    It creates a mapper on the fly if not provided and will use
    InspectMapper to know how to behave for each field. InspectMapper is 
    SqlMask.fields

    If no layout is provided it will be created on the fly.

    The layout is analized to understand wich fields are to be represented,
    in case a menubar and a toolbar are added.

    Fields will be shown in appropriate widgets:

      - gtk.Entry for Strings and integers (le latter are right aligned if
        they're not foreign keys)
      - dateedit.dateedit for dates and timestamp
      - gtk.Checkbox for bool

    All fields will have a label that is sensible to mouse clicks. A mouse
    click pops up a filter widget
    
    All entries that represent fields or foreign keys are sensible to
    right-clik, F1 and Control-F1 that allows the completion of the values to
    occur. 


Completion
===========

    Completion works well for entries in the mapper and for entries that
    point to a foreign table/fkey.
    
    The ListStore used for the completion is only filled on demand (right
    click or F1/C-F1) and the string already in the entry is used as
    whereclause condition, ~* is used as operator.

    The list is normally initialized with 1 column, 2 columns in case of
    foreign key: the first is the real data, the second is the information
    shown in the completion and in the entry. The real info is stored in 
    self.values[field_name]. self._get_values, the method that retrieves the
    data from the gtk widgets gets it from there.
