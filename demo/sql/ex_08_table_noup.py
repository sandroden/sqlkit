"""base/options: noup 

year and description will not be editable (but they can be changed
programmatically)


"""

t = SqlTable(table='movie',
             dbproxy=db,
             order_by='director_id',
             noup='year, description',
         )


t.reload()

