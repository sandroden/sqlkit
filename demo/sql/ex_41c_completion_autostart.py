"""completion/enum m2m

Completion may be configured to act as an enum, normally only if
the remote table has only a few elements. In that case the list of possibilities
is shown completely regardless of what is written in the field.

"""

lay = """
   title
   year
   director_id
   m2m=genres -
"""

t = SqlMask(model.Movie, dbproxy=db, layout=lay)
t.related.genres.completions.name.autostart = 2
t.related.genres.completions.name.force_enum = True
