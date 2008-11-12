"""base/movie mask

base editing mode: mask view
"""

lay = """
   first_name
   last_name
   nation
"""

t = SqlMask(table='director', dbproxy=db, layout=lay, geom=(800,600))
t.reload()

lay2 = """
    title
    date_release
    L=description TXS=description
    director_id
    """
t2 = SqlMask(table='movie', dbproxy=db, layout=lay2)
t2.reload()
