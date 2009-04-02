"""completion/group by

the values shown in a completion may be grouped 
try completion on 
"""

lay = """
    title
    year
    director_id
"""

t = SqlTable(class_=model.Movie, dbproxy=db, layout=lay)
t.completions.director_id.group_by = 'nation'



