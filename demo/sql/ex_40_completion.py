"""completion/basic

Completion is the way you can save typing. When completion is invoked, entry
completion is used to show possible completions. If the field is a foreign key,
completion is done against the value of the foreign key (i.e. not the id). The
value is searched for via the attribute that better represents the record,
or declared as search field for the table, or the first char field.

You can invoke completion via Control-Return in any field and by clicking on the
down arrow for a foreign key.

Completion works both in Table view and Mask view.

Completion on a field that is not a foreign key returns a selection of values
of the field.

Completion has 2 flavours: start and regexp: see docs

You don't need to do anything particular to start a plain/basic completion

"""

lay = """
   title
   year
   director_id
   date_release
"""

t = SqlMask(model.Movie, dbproxy=db, layout=lay)
