"""base/movie mask

base editing mode: mask view
"""

lay = """
   first_name
   last_name
   nation
"""

lay2 = """
    title
    date_release
    TXS=description 
    director_id
    """
t = SqlMask(table='movie', dbproxy=db, layout=lay2)
t.reload()
