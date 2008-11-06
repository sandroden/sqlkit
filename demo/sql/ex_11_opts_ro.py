"""base/options: ro

read-only set all columns as not updateable
"""

t = SqlTable(table='movie',
             dbproxy=db,
             order_by='director_id',
             ro = True,
         )


t.reload()

