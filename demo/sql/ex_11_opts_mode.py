"""base/options: mode

The mode of the widget (UPDATE, DELETE, INSERT and BROWSE) can be set/revoked.
read-only sets all columns as not updateable
"""

t = SqlTable('movie', dbproxy=db,   order_by='director_id',)
t.mode = '-iu'  # revoke INSERT and UPDATE
t.reload()

t2 = SqlMask('movie', dbproxy=db,   order_by='director_id',)
t2.mode = '-bu'  # revoke BROWSE and UPDATE (but new objects can still be inserted)

t2.reload()
