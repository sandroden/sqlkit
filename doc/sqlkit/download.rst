=========================
 Download & requirements
=========================


requirements
============

Sqlkit depends on:

  * Python
  * Pygtk
  * sqlalchemy (>=0.5)
  * glade2
  * dateutils 
  * the correct driver for your database of choice


download
========
The code is available under an hg repository::

  hg clone http://hg.argolinux.org/py/sqlkit
  
You can download sqlkit package from here_ in tar or deb format.
You can also add the source::

  deb http://apt.argolinux.org/ lenny sqlkit

and install it via::

  apt-get install python-sqlkit

Even if the source state ``lenny`` can safely be used for ubuntu and etch.

.. note:: Note
    
    sqlkit depends on sqlalchemy >= 0.5 that is not yet packaged by ubuntu
    so the .deb does not require it. Please make sure to install it::
    
       easy_install sqlalchemy










.. _here: http://docs.argolinux.org/sqlkit/sqlkit/download

  
