#!/usr/bin/env python

import sys

sys.path.append ('../../')
import sqlkit as sk
import dbg
import gtk
import decimal

from sqlalchemy import *

engine = sk.config.new_engine(echo=False, globalconn=True)
session = create_session()
meta = default_metadata

user_table = Table ('euro_user', engine, autoload=True)

class Mapper(object):
    pass
user_mapper = mapper (Mapper, user_table)

sql_text = "user_id > 5"
zz = user_mask = sk.SqlMask (mapper=user_mapper, sql=sql_text, show=False,
                             noup='user_active', single=True, limit=2,
                             session=session)

zz.show()

## Completion - you may choose how to show the completion list
## default is the first ending with _name or _descr
## NOTE: may also precede call to SqlMask
format = None
format = "%(city_name)-5.5s (%(city_pv)s)"

sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', format)

engine.echo = True
#dbg.gtk_dbg.ShowClassInfo(zz)
#print dir()
gtk.main()


