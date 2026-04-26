"""completion/autostart m2m

Completion may start automatically after n digits are entered
Try writing 2 letters (eg.: 'fa')

"""

lay = """
   title
   year
   director_id
   m2m=genres -
"""

t = SqlMask(model.Movie, dbproxy=db, layout=lay)
t.related.genres.completions.name.autostart = 2
