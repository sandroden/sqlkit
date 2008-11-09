"""base/options: geom

read-only set all columns as not updateable
"""

t = SqlTable(table='movie',
             dbproxy=db,
             order_by='director_id',
             geom = (700, 500),
         )


t.reload()

