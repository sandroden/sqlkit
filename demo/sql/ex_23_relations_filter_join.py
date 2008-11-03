"""relation/o2m: reload filter panel

roreload from the filter panel is slightely different: it shows the result
in a page of the filter panel. str(obj) is used to represent the records.
"""

lay = """
   first_name
   last_name
   nation
   m2m=movies::title,year -
"""

t = SqlMask(Class=model.Director, dbproxy=db, layout=lay)
t.add_filter(movies__title__iregexp='il')
t.add_filter(first_name__iregexp='a')
t.reload()

