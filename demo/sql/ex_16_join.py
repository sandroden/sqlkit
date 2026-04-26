"""base/join

You can edit the join of 2 tables just using tables='table1 table2'

Note that in a join you need to filter/add a constraint on a name that is
a composition of the table and the field_name

"""

t = SqlTable("movie director", dbproxy=db)
t.add_filter(director_nation='IT')  # NOTE director_nation
t.reload()
