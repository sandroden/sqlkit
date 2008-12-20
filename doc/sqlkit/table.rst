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

:set_editable:
   only meaningful for table that represent an m2m relationship: turns the
   table from non eidtable to editable, read the explanation in
   :ref:`relationship`

:hide_field:
   hides columns, adding a row in the menu to make it show up again at will 
   
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


Export
=======

A very minimal export function allow to export visible data in a csv (comma
separated value) format. Follow File -> Export.
