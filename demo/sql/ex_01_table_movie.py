"""base/movie table

base editing mode: table view
"""

t = SqlTable(table='director',
         dbproxy=db,
         order_by='last_name',
         rows=6,
         )
t.reload()

