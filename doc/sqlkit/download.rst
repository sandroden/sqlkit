=======================================
 Download & requirements & googlegroup
=======================================
  

Requirements
============

Sqlkit depends on:

    * Python
      * Pygtk
      * sqlalchemy (>=0.5.3)
      * glade2
    * dateutils 
    * the correct driver for your database of choice
    * babel (localization)

Changelog
===========

this is the Changelog_

.. _Changelog: http://sqlkit.argolinux.org/download/Changelog

Download
========
The code is available under an hg repository::

  hg clone http://hg.argolinux.org/py/sqlkit
  
You can download sqlkit package xxxx from here_ in tar or deb format. 


+-----------------------------------+----------------------------------------------------+
|Python package                     |sqlkit-xxxx.tar.gz_                                 |
+-----------------------------------+----------------------------------------------------+
|Debian package                     |python-sqlkit-xxxx_all.deb_                         |       
+-----------------------------------+----------------------------------------------------+
|Debian documentation package       |sqlkit-doc_xxxx_all.deb_                            |       
+-----------------------------------+----------------------------------------------------+
|Linux executable (pyinstaller)     |sqledit-binary-xxxx.tar.gz_ (not yet ready)         |
+-----------------------------------+----------------------------------------------------+
|Windows executable (pyinstaller)   |sqledit-binary-xxxx.exe_ (not yet ready)            |
+-----------------------------------+----------------------------------------------------+

Sqlkit is used in a production environment and great care is put in fixing
any bug as soon as possible. The first stable version will be 0.8.6. Present
version 0.8.6-rc5 should be almost ready. When 0.8.6 will be release new
features will be instroduced in a development branch.

I really appreciate any bug report particularly if based on a repeatable
example, possibily starting from the demo.

Binary boundles
===============

Since sqlkit depends on several different packages we also provide a boundle
with an installer that you can use to run the demo and the command sqledit
for sqlite, mysql and postgres databases. 

It does not have any dependacies.

You cannot use it to build other executables. If all you want to do is using
the command sqledit, that's a good choice (probably a little slower to open).

Debian/Ubuntu
=============

You can also add the source::

  deb http://apt.argolinux.org/ lenny sqlkit

you will probably want to add the key:

  sudo wget -q http://deb.argolinux.org/apt.key -O- | sudo apt-key add - 
  sudo apt-get update

and install it via::

  apt-get install python-sqlkit

Even if the source states ``lenny`` it can safely be used for ubuntu.

.. note:: Sqlalchemy
    
    sqlkit depends on sqlalchemy >= 0.5 that is not yet packaged by ubuntu
    so the .deb does not require it. You can get it from Debian
    Experimental_ and it will install also in ubuntu

.. note:: Babel

   sqlkit depends on babel that is not packaged in debian but is packaged in
   ubuntu with two different names in hardy and jaunty and is missing in
   intrepid. So the package I have prepared does not depend on it. You are
   supposed to add the package. If using hardy install ``python-babel`` if
   using jaunty, use ``python-pybabel`` instead. If using intrepid... I'm
   almost sure there was a pybabel, but there is no more... install by
   hand!::

      easy_install babel

Mailing list
============

You can join our mailing list_

Localization
============

We need the help from some translator to localize in different languages. It
takes some 20 minutes to provide a complete set of translations for each
language. Please visit the launchpad_ 's site or contact me directly.

Author
======

Sqlkit is developed by `Alessandro Dentella`_


.. _list: http://groups.google.com/group/sqlkit
.. _here: http://sqlkit.argolinux.org/download/
.. _Experimental: http://packages.debian.org/experimental/python-sqlalchemy
  
.. _sqlkit-xxxx.tar.gz: http://sqlkit.argolinux.org/download/sqlkit-xxxx.tar.gz
.. _python-sqlkit-xxxx_all.deb: http://sqlkit.argolinux.org/download/python-sqlkit-xxxx_all.deb
.. _sqledit-binary-xxxx.tar.gz: http://sqlkit.argolinux.org/download/sqlkit-pyinstaller-xxxx.bin_
.. _sqledit-binary-xxxx.exe: http://sqlkit.argolinux.org/download/sqlkit-pyinstaller-xxxx.exe_
.. _sqlkit-doc_xxxx_all.deb: http://sqlkit.argolinux.org/download/sqlkit-doc_xxxx_all.deb
.. _`Alessandro Dentella`: mailto:sandro@e-den.it
.. _launchpad: https://launchpad.net/sqlkit
