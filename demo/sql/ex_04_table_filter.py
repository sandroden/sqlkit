"""base/filters

This is one of the key points of sqlkit.

A filter can be added with django_like syntax
"""

t = SqlTable('director', dbproxy=db,  order_by='last_name',)
t.add_filter(last_name__icontains='a')
t.reload()
