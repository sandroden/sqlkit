.. _completion:

============
 Completion
============

Complietion is the way you can avoid writing too much if the system already
has your data. It comes in two *flavours*:

  1. completions on the same column (eg.: data that you have already written
     in other records). This is only available for char/text fields.

     No check is made in this field, the text can be further edited

  2. completion on foreign key. A check is made, no way to input a text that
     is not matched on the remote field (see :ref:`description` below)

The match of the completion have two *modes*:

  :start: partially written text is used as a filter and completion must
    match from the start of the field. It uses LIKE operator

  :regexp: the match is done via regular expression id db supports it or via
    LIKE operator adding ``%`` on both sides

Since completion implies a search that may return *many* records, it's only
triggered on demand. Normal binding are:

  :shift   Return: triggers 'start' mode completion
  :control Return: triggers 'regexp' mode completion. This is also triggered 
                   pressing the down arrow of a foreign key

behaviour on completion
========================

When the completion is in a SqlTable that represents an m2m relationship (as
``actors`` would be for ``movies``), the completions does not simply add the
single field but substitutes the whole record.


autocompletion
==============

You can force completion to start after n chars has been entered setting the
completion object ``autostart`` value::

  t = SqlMask(table='movie', dbproxy=db)
  t.completions.director_id.autostart = 2

Completion will be recalculated any time the written string is shorter that
the last text that triggered the completion.

Take care not to use a little value for ``autostart`` on large tables.

completion and Return in Tables
--------------------------------

There is another situation in which a completion is started
automatically. When editing a foreign key (or an m2m): if a ``Return`` is
hit, a select is issued to check if it's a valid value and if not that value
is used as base for completion. The difference from triggering a normal
completion is that if a valid value is found, no further completion is done.


caveats
=======

Since completion uses the already written chars to filter possible solution,
if you further delete such chars you are not seeing all the real possible
solutions but only the already retrieved ones. You can request a new
completion... 

.. _description:

foreign key description
========================

A foreign key is normally substitued by a more descriptive text.

When completing a foreign key the completion puts in the EntryCompletion a
description of the foreign reference that can be customized via normal
python format strings. You would use module sqlkit.db.utils and create an
object TableDescr::

  from sqlkit.db.utils import TableDescr
  utils.TableDescr('movie', format='%(title)s - %(year)s', metadata=db.metadata)

metadata is necessary so that TableDescr knows where to go and autoload
Table to introspect it, for internal purpouses.

group_by
========

Theres also en easy possibility to add grouping of completion via a
foreign_key attribute. It's enought to set the group_by attribute of
completion_group_by::

  t.completions.director_id.group_by = 'nation'

.. image:: ../img/completion_group_by.png
