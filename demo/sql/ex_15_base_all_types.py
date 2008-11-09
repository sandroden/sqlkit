"""base/all types

simple mask showing all supported types. Some are clearly poorely rendered
as interval and NullableBool (that it not working at all).


"""

t = SqlMask(Class=model.AllTypes, dbproxy=db )
t.reload()

t1 = SqlTable(Class=model.AllTypes, dbproxy=db )
t1.reload()

