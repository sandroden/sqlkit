"""printing/related foreign key


"""

lay = """
  name
  m2m=movies:title,year,director_id - -
"""

t = SqlMask(model.Genre, layout=lay, dbproxy=db)
t.printing.add_menu_entry('Print to pdf', 'genres-fk.odt', mode='pdf', accel='<Alt>p')
t.reload()


