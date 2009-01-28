=======================================
 Download & requirements & googlegroup
=======================================


requirements
============

Sqlkit depends on:

  * Python
  * Pygtk
  * sqlalchemy (>=0.5)
  * glade2
  * dateutils 
  * the correct driver for your database of choice
  * babel (for localization)

changelog
===========

this is the Changelog_

.. _Changelog: http://sqlkit.argolinux.org/download/Changelog

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
    so the .deb does not require it. You can get it from Debian
    Experimental_ and it will install also in ubuntu

.. note:: Babel

   sqlkit depends on babel that is not packeged in debian but is packaged in
   ubuntu with two different names in hardy and intrepid. So the package I
   have prepared does not depend on it. You are supposed to add the
   package. If using hardy install ``python-babel`` is using intrepid, use 
   ``python-pybabel``

mailing list
============

You can join our mailing list_

.. _list: http://groups.google.com/group/sqlkit
.. _here: http://sqlkit.argolinux.org/download/
.. _Experimental: http://packages.debian.org/experimental/python-sqlalchemy
  
