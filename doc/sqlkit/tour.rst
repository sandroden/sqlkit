======================= 
Sqlkit feature's tour
=======================

Main features of sqlkit:

 - editor of databases in 2 modes: table & mask
 - based on sqlalchemy: can cope with many different databases
 - very powerfull filtering capabilities
 - completion both on local same field and foreign key fields
 - very easy way to draw a layout for mask views
 - sqledit: python script to edit db

Views
======

Two possible views: table & mask

.. image:: ../img/viste.png

that where requeted by the following instructions::

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
=========


Each label of both views can be clicked to get a filter panel:
   
.. image:: ../img/filter-panel.png

Completion
============

Completion is triggered by F1 key. If the field is a foreign key it will pop
up a list of foreign values (broken at the moment) otherwise it will show
values cirrently used (just for varchar fields)


Layout
========

Very easy way to draw a layout. See :ref:`layout` widgets for a tour.


Sqledit
=========

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


  
