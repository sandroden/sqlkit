#!/usr/bin/env python

import sys

sys.path.append ('../../')
import sqlkit as sk
from sqlkit.table import SqlWidgetTreeView
import dbg
import gtk

from sqlalchemy import *

engine = sk.config.spawnEngine(echo=False)


zz = sk.SqlMask (table='euro_user', engine=engine)

z2 = SqlWidgetTreeView(table='euro_mail', engine=engine, naked=True)
print sk.inspect.get_join_cnd([zz.fields.mapper.primarytable,
                              z2.fields.mapper.primarytable], mode='str')
zz.sync_add(z2)
zz.reload()


## Completion - you may choose how to show the completion list
## default is the first ending with _name or _descr
## NOTE: may also precede call to SqlMask

sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', None)

#dbg.gtk_dbg.ShowClassInfo(zz)
#print dir()
gtk.main()


