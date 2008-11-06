"""base/options: noup 

year and dascription will not be editable (but they can be changed
programmatically)

Now a bug in the cell renderer for dates makes it impossible to make dates
not editable.

"""

t = SqlTable(table='movie',
             dbproxy=db,
             order_by='director_id',
             noup='year, description',
         )


t.reload()

