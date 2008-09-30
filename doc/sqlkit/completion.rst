.. _completion:

============
 Completion
============

Complietion is the way you can avoid writing too much if the system already
has your data. It comes in two *flavours*:

  1. completions on the same column (eg.: data that you have already written
     in other records). This is only available for char/text fields

  2. completion on foreign key

The match of the completion have two *modes*:

  :start: partially written text is used as a filter and completion must
    match from the start of the field. It uses LIKE operator

  :regexp: the match is done via regular expression id db supports it or via
    LIKE operator adding ``%`` on both sides

Since completion implies a search in possibly many fields, it's only
triggered on demand. Normal binding is:

  :shift   Return: triggers 'start' mode completion
  :control Return: triggers 'regexp' mode completion. This is also triggered 
                   pressing the down arrow of a foreign key
  
autocompletion
==============

You can force completion to start after n chars has been entered setting the
completion object ``autostart`` value::

  t = SqlMask(table='movie', dbproxy=db)
  t.completions.director_id.autostart = 2

Completion will be recalculated any time the written string is shorter that
the last text that triggered the completion.

Take care not to use a little value for ``autostart`` on large tables.


caveats
=======

Since completion uses the already written chars to filter possible solution,
if you further delete such chars you are not seeing all the real possible
solutions but only the already retrieved ones. You can request a new
completion... 

.. _descriptions:

foreign key description
========================

When completing a foreign key the completion puts in the completion a
description of the foreign reference that can be customized via normal
python format strings. You would use module sqlkit.db.utils and create an
object TableDescr::

  from sqlkit.db.utils import TableDescr
  utils.TableDescr('movie', format='%(title)s - %(year)s', metadata=db.metadata)

metadata is necessary so that TableDescr knows where to go and autoload
Table to introspect it, for internal purpouses.
