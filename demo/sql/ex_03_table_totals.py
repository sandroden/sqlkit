"""base/totals

A stupid example to show the total on an integer
"""

t = SqlTable(table='movie',
         dbproxy=db,
         order_by='director_id',
         )

t.totals.add_total('year')
t.totals.add_break('director_id')

t.reload()

