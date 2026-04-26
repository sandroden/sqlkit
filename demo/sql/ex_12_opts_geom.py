"""base/options: geom

read-only sets all columns as not updateable
"""

t = SqlMask('movie',
            dbproxy=db,
            order_by='director_id',
            geom=(1000, 500),
            )


t.reload()
