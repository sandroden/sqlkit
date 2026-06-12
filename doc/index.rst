=========================================
sqlkit — edit your database the easy way
=========================================

**sqlkit** is a toolkit to edit the **data** of a database (as opposed to its
schema) in the easiest possible way. It is built on GTK 3 (PyGObject) and
SQLAlchemy_ and works with many backends: PostgreSQL, MySQL, SQLite and
Firebird.

By *easy* we mean both: easy for the **user**, since completion, filtering and
relationship editing come for free, and easy for the **programmer**, since a
lot of features are there to help you customize the interface with very little
code.

sqlkit provides:

* :doc:`sqledit <misc/sqledit>` — a GUI that can be used standalone and
  requires no programming knowledge: just point it at a database URL and start
  editing.
* a Python package built around two megawidgets — :doc:`SqlMask <sqlkit/mask>`
  and :doc:`SqlTable <sqlkit/table>` — powerful classes to build your own
  application.

A typical usage looks like this::

   from sqlkit.widgets import SqlTable, SqlMask
   from sqlkit import DbProxy

   db = DbProxy(engine='sqlite:///movies.sqlite')
   t = SqlMask('movie', dbproxy=db, single=True)

that pops up an editor for the record. A filter panel is available just by
clicking on the label of a field.

Highlights
==========

* Edit databases in two modes — :doc:`table <sqlkit/table>` and
  :doc:`mask <sqlkit/mask>`. A mask can embed tables of
  :doc:`related records <sqlkit/relationship>`.
* Powerful :doc:`filtering <sqlkit/filters>`: every field can filter visible
  records, including dates on a relative basis and fields in related tables.
* :doc:`completion <sqlkit/completion>` on both normal and foreign-key fields.
* A concise :doc:`layout language <layout/contents>` to draw mask views.
* Effortless editing of :doc:`relationships <sqlkit/relationship>` (m2o, o2m,
  m2m) and easy :doc:`defaults <sqlkit/defaults>`.
* :doc:`totals and subtotals <sqlkit/totals>` in numeric columns.
* :doc:`constraints <sqlkit/constraints>` expressed as SQLAlchemy queries or
  with a Django-like syntax.
* Signals and :doc:`hooks <sqlkit/validation>` for easy customization and
  validation, plus more than 70 runnable snippets in the demo.

.. _SQLAlchemy: https://www.sqlalchemy.org

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   Sqlkit <sqlkit/contents>
   Sqledit <misc/sqledit>
   Tutorials <misc/tutorials>
   Layout <layout/contents>
   Debug <debug/contents>
   Download <misc/contents>
