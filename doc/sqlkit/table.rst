.. _table:

===========
 SqlTables
===========

SqlTable is a widget that represent data in a table mode. Columns that are
foreign keys are presented in blue and a :ref:`description <description>` of
the foreign key is used.

Clicking on any row of the treeview gives the possibility to show the record
in a Mask View. If a layout was passed to the ``SqlTable``, it will be
passed to SqlMask.


Options
=======

.. class:: sqlkit.widgets.Sqlwidget(same options as sqlwidget + listed below)

  :param rows:  how many rows should be initially allocated space for

Attributes
==========

.. attribute:: totals

   class for :ref:`totals`: see the specific documentation for further info

.. image:: ../img/menu.png
   :align: right

Methods
=======

.. method:: set_opts(scroll=None, icons=True)

   :param scroll: eliminate scrollbars (values: x|y|xy|None)

   :param icons: allows to disable icons in a m2m relationship
   :type scroll: boolean 
   

.. method:: set_editable(editable)

   :param editable: Only meaningful for table that represent an
          m2m relationship: turns the table from non editable to editable, 
	  read the explanation in :ref:`relationships`
   :type editable: boolean

.. method:: hide_fields(field_list)

   :param field_list:  hides columns, adding a row in the menu to make it
          show up again at will 
   
.. method:: select_path(path=None, obj=None)

   :param path:  the path to be selected or None
   :param obj:  if path is None, the object to be searched for and selected

   
Column headers
==============

Each column is clickable. Clicking on the column pops up a menu that enables:

 - to add a filter on this field (see :ref:`filters`)
 - to sort on this field (database sorting)
 - to add a total on this column (if the column is numeric)
 - to add a brake on this column (see docs for :ref:`totals`)


Cell renderers
==============


Boolean
---------

Booleans are represented with CellRendererToggle, if the field is nullable,
the value loops over 3 states.

Text
----

I don't have a satisfactory CellRender for long text. Any hint is appreciated.


Export
=======

A very minimal export function allows to export visible data in a csv (comma
separated value) format. Follow File -> Export.

Shortcut
========

in the treeeview
----------------

:Control-x:  eliminates a line
:Control-k:  eliminates a line 
:Control-s:  saves the record
:Control-q:  quits the table
:Control-n:  opens a new record

in the editable cell
--------------------
:Control-Enter: pops a completion (regexp mode)
:Shift-Enter:   pops a completion (start mode)
:Esc:           aborts editing 


Signals
=======

:button-press-event: this event is emitted when clicking in the treeview if
       there are no pending validation errors (in which case you are forced
       to solve them before). It is mainly used to handle the default
       menu. Look in the example to see how you can manipulate the menu.


  .. method:: button_press_cb(table, event, obj, field_name, menu)
 
     :param table: the SqlTable that emitted the signal
     :param event: the gtk.gdk.Event associated
     :param obj: the object currently selected or None
     :param field_name: the field_name of the selected column
     :param menu: the default menu that il popped up by this
          button-press-event if event.button == 3 or None
     


