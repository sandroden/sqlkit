=======================================
 Download, requirements & googlegroup
=======================================
  

Requirements
============

Sqlkit depends on:

       * Python
       * Pygtk
       * sqlalchemy (>=0.5.3). Rel 0.9.0 is the first sqlkit release
         that works with sqlalchemy 0.6+
       * glade2
       * python-dateutils 
       * setuptools
       * the correct driver for your database of choice among the backend
         `supported by sqlalchemy`_
       * babel (localization)

Changelog
===========

this is the Changelog_

.. _Changelog: http://sqlkit.argolinux.org/download/Changelog

Download
========
The code is available under an hg repository::

  hg clone http://hg.argolinux.org/py/sqlkit
  
You can download sqlkit package VER from here_ in tar or zip format. 

+--------------------------------------+-------------------------------------+
| Python package                       |* sqlkit-VER.tar.gz_                 |
|                                      |* sqlkit-VER.zip_                    |
+--------------------------------------+-------------------------------------+


Sqlkit is used in a production environment and great care is put in fixing
any bug as soon as possible. The first stable version has been 0.8.6 in 2008. 

I really appreciate any bug report particularly if based on a repeatable
example, possibly starting from the demo.

Windows
=======

I'm not a window guy and it always takes me quite long to setup things
correctly, anyhow this is a working recepy, aimed at minimum effort:

 * `Python from ActiveState`_ (it already sets Python in the PATH. Watch out
      for licence, otherwise do all by hand: install python27_ and set PATH
      accordingly) 

 * `PyGTK-all installer`_ by Dieter Verfaillie (Note that it's a testing
      bundle but I found it ok provided you use it with a fairly new
      installer engine e.g. SP2 on XP)

 * unzip sqlkit and install it simply by running::

      > python setup.py install

   at this point you should be able to move to demo and run it::

      > cd demo\sql
      > python demo.py

.. _`PyGTK-all installer`: https://github.com/dieterv/pygtk-installer/downloads
.. _Python27: http://www.python.org/ftp/python/2.7/python-2.7.msi
.. _`Python from ActiveState`: http://downloads.activestate.com/ActivePython/releases/2.7.0.2/ActivePython-2.7.0.2-win32-x86.msi

.. _Python26: http://downloads.activestate.com/ActivePython/releases/2.6.6.15/ActivePython-2.6.6.15-win32-x86.msi
.. http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi
.. _`GTK + glade`:  http://ftp.gnome.org/pub/GNOME/binaries/win32/glade3/3.6/glade3-3.6.7-with-GTK+.exe
.. _PyGTK: http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.16/pygtk-2.16.0+glade.win32-py2.6.exe
.. PyCairo: http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/1.8/pycairo-1.8.6.win32-py2.6.exe
.. Pygobject: http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/2.20/pygobject-2.20.0.win32-py2.6.exe


Debian/Ubuntu
=============

If you want a bleeding edge sqlkit version you'd better install from the
package distribution. On a Debian lenny or Ubuntu >= 9.04 you can prepare
dependencies::

  sudo wget http://apt.argolinux.org/sqlkit.list --output-document=/etc/apt/sources.list.d/sqlkit.list
  sudo wget -O-  http://apt.argolinux.org/dists/lenny/public.key| sudo apt-key add -
  sudo apt-get update
 
and install it as follows (this installs python drivers for PposgreSQL and
Mysql as well)::

apt-get install python-sqlkit python-psycopg2 python-mysqldb

I'll try to keep this updated as the official package

Windows
=======

Sqlkit depends on PyGTK. Thanks to  Dieter Verfaillie now it's possible to
install PyGTK in a single boundle. Detailed information in the tutorial_.

Sqlkit on  Pypi 
=================

Sqlkit is now available via Pypi (Python package index), so -if you have
already installed setuptools that provides the command easy_install- you can
install it via ``easy_install`` or better ``pip``::

  easy_install pip
  pip install sqlkit

You can also install directly with ``easy_install`` that often will fail
understanding already installed packages. Should you have problems with ``pip``
you can revert to::

  easy_install sqlkit


No one of these command will install the backend driver (psycopg2 for
postgresql, MySQLdb for mysql,...) that you are supposed to
install by yourself. Sqlite is included in Python stadard library.


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
  
.. _sqlkit-VER.tar.gz: http://sqlkit.argolinux.org/download/sqlkit-VER.tar.gz
.. _sqlkit-VER.zip: http://sqlkit.argolinux.org/download/sqlkit-VER.zip
.. _python-sqlkit_DEBVER_all.deb: http://sqlkit.argolinux.org/download/python-sqlkit_DEBVER_all.deb
.. _sqledit-binary-LNXVER.tar.gz: http://sqlkit.argolinux.org/download/sqledit-binary-LNXVER.tar.gz
.. _sqledit-setup-WINVER.exe: http://sqlkit.argolinux.org/download/sqledit-setup-WINVER.exe
.. _sqlkit-doc_VER_all.deb: http://sqlkit.argolinux.org/download/sqlkiy-doc_VER_all.deb
.. _`Alessandro Dentella`: mailto:sandro@e-den.it
.. _launchpad: https://launchpad.net/sqlkit
.. _`supported by sqlalchemy`: http://www.sqlalchemy.org/trac/wiki/DatabaseNotes
