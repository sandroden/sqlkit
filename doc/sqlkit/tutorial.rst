==================
 Sqledit Tutorial
==================

Intro
=====

This is meant as a tutorial for the sqledit command that is part of
sqlkit. It's intended audience is anybody who is interested in editing data
in a database (as opposed to editing the *structure* of the database).

No programming skill is required, but if you are supopsed to install it
yourself, you may need to understand at least a little bit of your operating
system.


Installation
============

Boundles
---------

The only possibly difficult part of installation may be the installation of
the dependencies. To bypass this I also provide binaries that bundle
toghether any required software for Linux or Windows (you can donwload it
from the `download page`_). Drivers for postgres, mysql and sqlite are
included. 

The hard way
-------------

If you prefere to do it the hard way, or if you meet problems with the
boundle, or you need more backend drivers, you need to do the following steps.

Dependencies
------------

:pygtk:  any Linux desktop distribution already has it installed, in case
         it does not have it, it should be trivial to do. In debian like
         systems (eg.: Ubuntu), you simply run::

 	     apt-get install python-gtk2

         In a Windows system it's a much more difficult task. Please follow
         the instructions on the `pygtk site`_

:sqlalchemy: this is the core of the sql staff. It's a layer that builds SQL
         statements and invokes the backend drivers. It takes care of
         inspecing the database and so on. You need at least release 0.5 but
         0.5.4 would be much better. 

:python-dateutil: needed for computation on dates, used in filters (eg: date
         >= 'm-1', means date >= starting of last month), see doc page_


:babel:   needed for localization of numbers and dates
          
:drivers: don't forget to add the driver for the backend of your choice, the
          only driver included is for ``sqlite``, that is the database of
          the demo and is included in the python distribution since python
          2.5. The boundle has drivers for postgres and mysql as well.
	  

If you have setuptools installed in your system, you can install whatever
you need simply with::

   easy_install sqlkit

and probably you'd have better results using ``pip``::

   easy_install pip
   pip install sqlkit


Installing under Debian/Ubuntu
-------------------------------

If you have a debian like distro I suggest you install sqlalchemy from
source or via easy_install or pip and then install the debian package::

  sudo wget http://apt.argolinux.org/sqlkit.list --output-document=/etc/apt/sources.list.d/sqlkit.list
  sudo wget -O-  http://apt.argolinux.org/dists/lenny/public.key| sudo apt-key add -
  sudo apt-get update
 
and install it via::

  apt-get install python-sqlkit


sqledit/sqlkit
==============

.. image:: ../img/sqledit.png
   :align: right

Now you should have a working setup. The command we are going to familiarize
with is ``sqledit`` that is based on a library named ``sqlkit``. If you are
a programmer and are interested in the sqlkit package you can find extensive
documentation in the `web site`_

Programming with sqlkit is a pretty simple experience that allows to use
much more features than available with ``sqledit``, nevertheless you can do
a lot of simple tasks by usng ``sqledit`` alone.


Sqledit can be used:

* from command line, possibly adding arguments and options
* from a menu entry interactively writing the URL of the database you want to edit.

It yo start it with no arguments you are presented a dialog with and entry
and 3 buttons:

* you can write the url of a database of yours in the entry, eg.::

    postgres://localhost/dbname
    sqledit:///db.sqlite
    mysql://name:pass@host/dbname
  
  .. note::
     the URL for a sqlite database has 3 '/'if the database is in your
     corrent directory, 4 if you need to pass a file starting with '/'.

* start the demo tour

the demo tour
=============


The demo tour is meant for developers, so that it shows source code as well,
but it's also suitable for our introduction and is a living database, so we
will use that in this tutorial.

the demo presents you with some examples on the left. Let's start with...
the last one! We start with the last one becouse it's the tipe of thisn you
will see when you start sqledit with an address of a real database (the demo
one in this case).



The table listing
-----------------

of the database is as shown above: clicking on a table name pops a menu that
lets you choose between:

* table view: representation of the table in a spreadsheet fasion
* mask view:  a form with each field is displayed
* table reflection: sqledit reads the definition for that table

Let's choose a table view:


No time left. I'll finish later...

cheers
sandro
*:-)







.. _`download page`: http://sqlkit.argolinux.org/sqlkit/download.html
.. _`pygtk site`: http://www.pygtk.org
.. _`sqlalchemy site`: http://www.sqlalchemy.org
.. _page: http://sqlkit.argolinux.org/sqlkit/filters.html#module-sqlkit.misc.datetools
.. _`web site`: http://sqlkit.argolinux.org
