"""base/defaults

Defaults are set on the database table, not on the SqlMask/SqlTable

When setting the default for a foreign key, you can use the fk method that
sets it directly via the name. In that case you need to say which field you want
to use for SELECT
"""
from sqlkit.db import defaults

def_movie = defaults.Defaults('movie', metadata=db.metadata)
def_movie.set_defaults(
    {'date_release': def_movie.today,
     'title': 'A nice title...',
     })
def_movie.fk('director_id', 'last_name', 'Fellini')


#t = SqlMask('movie',  dbproxy=db,     )
t = SqlTable('movie',  dbproxy=db,)


## unregister to prevent conflicts in following examples
#del defaults.tables['movie']
