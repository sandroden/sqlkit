#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
import sqlkit as sk
import dbg
dbg.dbg = 1

from sqlalchemy import *
from layout import *

engine = sk.config.spawnEngine(echo=False)
user_table = Table ('euro_user', engine, autoload=True)
mail_table = Table ('city', engine, autoload=True)

class User(object): pass
class Mail(object): pass
#user_mapper = mapper (User, user_table)
mail_mapper = mapper (Mail, mail_table)

rel = relation(mail_mapper, lazy=False, )
m = mapper(User, user_table, properties = { 'mail' : rel } )
layout.map_labels(filename='label_map.txt')

lay = """
{h  {-|.a
      user_name
      user_last_name
    }
          {
             {-|>>.archivio
               user_birth_date
               user_sex
               user_age
               city_id
               city_pv

             }
             {-|>>.stato
               user_active
              user_timestamp
             }
    }
}   
"""


sql_text = "user_id > 5"
sql_text = "city_name ~* :city_name"
zz = user_mask = sk.mask.SqlMask (mapper=m, lay=lay)
#                                  sql=(sql_text, {'city_name':'mo'}))

gtk.main()


