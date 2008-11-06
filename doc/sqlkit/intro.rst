.. _sqlkit:

Sqlkit
=======


Sqlkit is a tool to edit __data__ in the easiest possible way, to be used
building applications that use databases. It is not an editor for tables
schemas: no way to add columns or add foreig key relationships is provided.

A tipical usage can be::


  from sqlkit import SqlTable, SqlMask, DbProxy
  
  db = DbProxy(engine='sqledit:///movies.sqlite')
  t = SqlMask(table='movie', dbproxy=db, single=True)
     
that will pop up an editor for the record. Filter panel will be available
just clicking on the label of the fields.



I assume that...
---------------------

1. You use PrimaryKeys and ForeignKeys throughout the db.
   If you don't use ForeignKeys sqlkit will just work w/o any special
   behaviour. If you don't use PrimaryKeys sqlkit will not even open the table.

2. You are using one single metadata. This is a limit but it's my normal
   environment. There's not really anything that cannot be changed easily
   about this, simply I didn't have need fo this, nor working cases.  (While
   I was plenty of ideas on other features...)

3. ForeignKey are simple... Again this is more due to the fact that I use it
   this way normally and I didn't have any example of use. 

.. _fkey:

ForeignKeys
--------------

Everywhere there's a ForeignKey (see point 3 above) I try to represent it in
the best possible way. More info in the completion chapter:
:ref:`description`


sqlkit supported backend structure
----------------------------------

1. sqlkit is built on sqlalchemy that allows editing db with many
   `different engines`_. I use it with postgres, mysql and sqlite. 
   Other engines are supported but need a very simple addition that I'd be
   willing to do on demand.

2. SqlMask/SqlTable must be fed a table or a mapper.

.. _`different engines`: http://www.sqlalchemy.org/docs/05/intro.html#overview_sqlalchemy_dbms
