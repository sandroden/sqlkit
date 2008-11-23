.. _table:

===========
 SqlTables
===========

SqlTable is a widget that represent data in a table fasion. Columns that are
foreign keys are presented in blue and a :ref:`description <description>` of
the foreign key is performed.


Options
=======

:rows: 
  how many rows should be initially allocated space for

Attributes
==========

:totals:
   class for :ref:`totals`: see the specific documentation for further info

.. image:: ../img/menu.png
   :align: right

Methods
=======

:set_opts:
   allows to disable icons in a m2m relationship (icons=False), eliminate
   scrollbars (scroll=x|y|xy|None)

Column headers
==============

Each column is clickable. Clicking on the column pops up a menu that enables:

 - to add a filter on this field (see :ref:`filters`)
 - to sort on this field (database sorting)
 - to add a total on this column (if the column is numeric)
 - to add a brake on this column (see docs for :ref:`totals`)


Cell renderers
==============

Dates
-----
Dates are represented with a CellRenderer that pops up up the calendar. I'm not
at all satisfied with this. Any hint is appreciated

Boolean
---------

Booleans are represented with CellRendererToggle, if the field is nullable,
the value loops over 3 states.

Text
----

I don't have a satisfactory CellRender for long text. Any hint is appreciated.
