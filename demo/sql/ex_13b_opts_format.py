"""base/options: format (numbers)

Numbers will be represented according to the active locale (according to
environment variables LC_NUMERIC, LC_ALL, LANG).

It's possible to force a different representation by setting 'format' and possibly
'locale' on the vfields. That can be done with the set_format method or via
the 'format' argument.
"""

t = SqlTable('movie',
             dbproxy=db,
             order_by='director_id',
             rows=15,
             format={'year': '#'},  # don't use group separator
             )


t.reload()
