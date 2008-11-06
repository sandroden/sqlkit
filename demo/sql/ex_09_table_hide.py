"""base/options: hide

year and description will not be visible

"""

t = SqlTable(table='movie',
             dbproxy=db,
             order_by='director_id',
             hide='year, description',
         )


t.reload()

