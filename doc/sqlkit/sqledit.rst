.. _sqledit:

=========
 Sqledit
=========


Sqledit is a data editor/browser. It may be called on a database and it will
present a list of all tables that can be selected for editing (choosing 
Mask or Table mode) or for introspection.

.. image:: ../img/sqledit.png

It has many options::

  """
  usage: %prog files [options] [[url|nick] table]
     -u, --url = URL: an url to open (eg postgres://user:pass@host/dbname)
     -n, --nick = nick: a nick in ~/.sqleditdb
     -t, --table = table: open table 'table'
     -m, --mask: open a SqlMask (default is SqlTable)
     -T, --sqltable: open a SqlTable (default when -t is used)
     -d, --dev: open in 'dev' mode
     -D, --debug: print debug
     -g, --gtk-debug: use LogTheMethods
     -S, --sql=statement: execute statement (requires -t)
     -a, --all-tables: read all table on startup (very slow)
     -f, --field_list=fields: comma (or space) separated field list 
     -o, --order_by=fields: comma separated field list
     -c, --configure: open SqlMasq on _sqlkit_table or create it

  """


.sqleditdb
============

You can write configurations in a file in your home calle ``.sqleditdb`` and
start sqledit on that configuration using a nickname::

   [invitati]
   URL = postgres://sandro:xxx@ny_host/2giugno
   table = partecipazioni_invitato
   dev = True
   field_list = nome, cognome, and all other fields
   order_by = cognome, nome

   [brasile]
   copy = invitati
   field_list = nome, cognome, email, ludo

  
Valid opion are URL and any other option for sqledit. The special option
``copy`` force sqledit to read the other definition first and then
overwrite.
In this case 'brasile' shares all optioons with '2giugno'  but overwrites
field_list.

