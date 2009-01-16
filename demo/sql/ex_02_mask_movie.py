"""base/movie mask

base editing mode: mask view
"""

lay = """
   first_name
   last_name
   nation
"""

t0 = SqlMask(table='director', dbproxy=db, layout=lay)
t0.resize(700, 500)
t0.reload()

lay2 = """
    title
    date_release
    L=description TXS=description
    director_id
    """
t = SqlMask(table='movie', dbproxy=db, layout=lay2)
t.reload()
