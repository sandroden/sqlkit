"""completion/autostart

Completion may start automatically after n digits are entered
Try writing 2 letters (eg.: 'fa')

"""

lay = """
   title
   year
   director_id
   date_release
"""

t = SqlMask(model.Movie, dbproxy=db, layout=lay)
t.completions.director_id.autostart = 2
