#!/usr/bin/env python

import sys

sys.path.append ('../../')
import sqlkit as sk
import dbg
import gtk

from sqlalchemy import *

engine = sk.config.new_engine(echo=False)


zz = sk.SqlMask (table='euro_user', engine=engine, nick='user')

z2 = sk.SqlMask (table='city', engine=engine, naked=True, nick='city')
zz.sync_add(z2)

## Completion - you may choose how to show the completion list
## default is the first ending with _name or _descr
## NOTE: may also precede call to SqlMask
format = None
format = "%(city_name)-5.5s (%(city_pv)s)"

sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', format)

#dbg.gtk_dbg.ShowClassInfo(zz)
#print dir()
gtk.main()


