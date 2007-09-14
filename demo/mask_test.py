#!/usr/bin/env python

import sys

sys.path.append ('../../')
sys.path.insert(0,'/usr/src/sqlalchemy/lib/')
import sqlkit as sk
import dbg
import gtk
import decimal

from sqlalchemy import *
from misc import rebuild
from ooffice import opop
dbg.debug(1)
engine = sk.config.new_engine(echo=False, globalconn=True)
session = create_session()
meta = default_metadata

user_table = Table ('euro_user', engine, autoload=True)
city_table = Table ('city', engine, autoload=True)

class Mapper(object):
    pass
#user_mapper = mapper (Mapper, user_table)

#sql_text = "user_id > 5"
zz = user_mask = sk.SqlMask (tables='euro_user, euro_mail', show=False,
                             noup=['user_active', 'user_age'], single=True, limit=20,
                             #filter="%(user_name)s (%(mail_address)s)",
                             filter=['user_name', 'mail_address'],
                             #filter=True,
                             nick='euro_user'
                             )

zz.print_template_dir = 'template_dir'
zz.show()


## Completion - you may choose how to show the completion list
## default is the first ending with _name or _descr
## NOTE: may also precede call to SqlMaskzz.filter_panel.set_reload(

format = None
format = "%(city_name)-5.5s (%(city_pv)s)"

sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', format)

rebuild.rebuild(sk.mask, doLog=True)

#engine.echo = True
#dbg.gtk_dbg.ShowClassInfo(zz)
#print dir()
gtk.main()


