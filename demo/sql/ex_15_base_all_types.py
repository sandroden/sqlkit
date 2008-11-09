"""base/all types

simple table showing all supported types. Some are clearly poorely rendered
as interval and NullabelBool (that it not workin at all).
"""

t = SqlMask(Class=model.AllTypes, dbproxy=db )
t.reload()


