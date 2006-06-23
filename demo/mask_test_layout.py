#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../')
#import py_path
#import config, reflect, mask
#import sqlkit as sk
import dbg
import layout
dbg.debug(True)

from sqlalchemy import *
import sqlkit as sk
#print dir(sk)
#print dir(sk.config)
from layout import *
#from validator import Validator

engine = sk.config.new_engine(echo=False, globalconn=True)
layout.map_labels(filename='label_map.txt')
session = create_session()

lay = """
{h  {-|.a user_name
        user_last_name
        b=premi -
    }
          {
             {-|>>.archivio
             user_birth_date
               user_sex
               user_age
               euro_mail.mail_address
               euro_mail.mail_notes
               city_id
#               city.city_pv

             }
             {-|>.stato
               user_active
#              user_timestamp
             }
    }
}   
"""
# sql="user_id > 5", 
zz = sk.SqlMask (table='euro_user', lay=lay, session=session)
format = "%(city_name)-5.5s (%(city_pv)s)"
sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', format)

#zz.lay_obj.prop('A.a', 'top-padding', 50)

gtk.main()


