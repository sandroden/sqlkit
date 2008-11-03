"""base/filters

a filter can be added with django_like syntax
"""

t = SqlTable(table='director',
         dbproxy=db,
         order_by='last_name',
         )
t.add_filter(first_name__iregexp='a')
t.reload()

