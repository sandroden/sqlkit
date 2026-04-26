"""completion/dynamic filter

A filter on completions may also be based on the value of another field at
the moment the completion is invoked.

Here the constraint is on nation. The completion of director is constrained by a possible value entered in nation.
"""

lay = """
   last_name
   nation
"""

from gi.repository import GLib
t = SqlMask(model.Director, dbproxy=db, layout=lay)

t.completions.last_name.filter(nation='$nation')

GLib.idle_add(t.set_value, 'nation', 'IT')

t2 = SqlMask(model.Director, dbproxy=db, layout=lay)
