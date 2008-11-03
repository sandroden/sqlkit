"""base/filters vs. constraints

a filter can be added with django_like syntax
"""

t = SqlTable(table='director', dbproxy=db,  order_by='last_name',  )
t.add_filter(last_name__iregexp='a')
t.reload()

t2 = SqlTable(table='director', dbproxy=db,  order_by='last_name',  )
t.add_constraint(last_name__iregexp='a')
t2.reload()
