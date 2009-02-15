"""completion/group by

the values shown in a completion may be grouped 
click o the down arrow...
"""

lay = """
    title
    year
    director_id
"""

t = SqlMask(class_=model.Movie, dbproxy=db, layout=lay)

t.completions.director_id.group_by = 'nation'


