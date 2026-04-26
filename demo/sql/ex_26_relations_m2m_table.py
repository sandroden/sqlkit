"""relation/m2m - different packing

Now the SqlTables for genres and actors are placed in a Table
that needs to be made to expand. You may notice that the separator
between genres and actors is no longer aligned with the end of the
title entry.
"""

from gi.repository import Gtk

lay = """
         title       year
         director_id - - -
         {T.a m2m=genres:5   m2m=actors } - - -
         """
t = SqlMask(model.Movie, dbproxy=db, layout=lay)

Tbl = t.widgets['T.a']
Tbl.set_vexpand(True)
Tbl.set_valign(Gtk.Align.FILL)
