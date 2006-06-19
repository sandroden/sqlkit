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

engine = sk.config.spawnEngine(echo=False, globalconn=True)
layout.map_labels(filename='label_map.txt')

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
               city_id
#               city.city_pv
               user_active
#              user_timestamp

             }
             {-|>>.mail
               {H b=gtk-delete.1  b=gtk-new.1} -
               
               euro_mail.mail_address
               euro_mail.mail_info
               euro_mail.mail_notes
             }
    }
}   
"""
zz = sk.SqlMask(table='euro_user', lay=lay, nick='user')
z1 = sk.SqlMask(table='euro_mail', lay=zz, nick='mail') 
zz.sync_add(z1)

# z1.lay_obj.disconnect('b=gtk-new',signal='clicked')
# z1.lay_obj.disconnect('b=gtk-delete',signal='clicked')
z1.lay_obj.connect(
    ('b=gtk-new.1','clicked', z1.record_clear),
    ('b=gtk-delete.1','clicked', z1.record_delete),
    )


#z1.record_clear()

format = "%(city_name)-5.5s (%(city_pv)s)"
sk.completion.set_description_fields(
    'city', 'city_name', 'city_pv', format)

#zz.lay_obj.prop('A.a', 'top-padding', 50)
dbg.gtk_dbg.ShowClassInfo(z1)

gtk.main()


