"""base/movie mask

base editing mode: mask view
"""

lay = """
   first_name
   last_name
   nation
"""

t = SqlMask(table='director', dbproxy=db, layout=lay)
t.reload()

