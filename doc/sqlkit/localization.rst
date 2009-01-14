.. _localization:

==============
 Localization
==============

localization support comprizes:

  * localization of number (decimal separators and thosand grouping)
  * localization of date/datetime fields
  * library messages translation
  * translation of field_name (see below)

Numbers and dates localization is provided by babel_

Numbers
=======

Numbers are represented according to your locale settings as follows:

:integer: grouping thousands  (format: '#.###')
:floats: grouping thousands, no limit on decimal (format: '#,###.#')
:decimals: grouping thousands, number of digits according to type.scale
  (format: '#,###.00', for Numeric(8,2))


forcing format representation
------------------------------

A different representation can be forced using `Number Format Pattern
Syntax`_ and setting the new values in the vfield class via the set_format
method that takes a dictionary as argument or the format argument to the widget::

  fmt = {
     'year'     : '#', # don't show thousand grouping
     'quantity' : ('#,###.#', 'en'),
  }
  t = SqlTable(.... format=fmt)  # fmt as argument
  t.set_format(fmt)              # fmt as method

where the two possible forms are shown. If the value is a tuple, the second
element is a locale to be used for the representation (as  `quantity` in the
example)

Dates
=====

dates are formatted according to your locale and the default format is
'short' for date/datetime and 'HH:mm' for time.

forcing format representation
------------------------------

A different representation can be forced using `Date Format Pattern
Syntax`_ and setting the new values in the vfield class via the set_format
as illustrated above for numbers.

.. note::

   for the time being this only works for ``SqlTable``, ``SqlMask``  uses a
   different widget that needs to be improved, so it's possible to set
   a different date format but not using babel.

   Temporarily you should set date_format attribute on the
   vfield.widget.gtkwidget...


Messages
=========

Translation of messages is provided by the standard gettext module. If you'd
like to contribute a translation for your language read the
README.localization in the distribution folder.

Translation of field_names of each column
------------------------------------------

Since many of the labels that appear in a mask and column headers of a table
default to the name of the column, it's important to add the possibility to
translate those strings as well, in order to give to the resulting mask a
friendly look.

The same column name may be translated differently in different tables so
sqlkit adds a layer in the way of translation via a "label_map" that can be
passed direcly to the layout object or to the sqlwidget (label_map option).

This ``label_map`` is a dictionary whose key is the ``field_name`` and the
value is a tuple with a description and a help_text to show as tooltip on
the label. Each of these are to be considered msgid that gettext can still
translate::

   { 'first_name' : ('First Name', 'Write the family name of the director')}

Description and help_text can be stored in the table ``_sqlkit_field`` that
can be easily edit with ``sqledit -c URL``. Each time a sqlwidget is
instantiated it will try to see if any info for the tables it is editing was
writtend in the database and add those to what can be passed to the widget
as "label_map".

Tooltips
----------

What we described is also the simpler way to add tooltips to labels and
buttons in your layout. This helps delegating to the customer the
personalization of the hints he wants to add to the GUI.

In the table ``_sqlkit_field`` each row should represent a field of a table, but
there's no harm adding to it more fields that can be the name of buttons or
relationships (eg.: author) just for the sake of translation and tooltip.


.. _`Number Format Pattern Syntax`: http://java.sun.com/docs/books/tutorial/i18n/format/decimalFormat.html#numberpattern
.. _`Date Format Pattern Syntax`: http://java.sun.com/docs/books/tutorial/i18n/format/dateFormat.html
.. _babel: http://babel.edgewall.org


