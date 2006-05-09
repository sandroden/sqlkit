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

engine = sk.config.spawnEngine(echo=False)
layout.map_labels(filename='label_map.txt')

lay = """
{h  {-|.a user_name
        user_last_name
    }
          {
             {-|>>.archivio
             user_birth_date
               user_sex
               user_age
               city_id

             }
             {-|>.stato
               user_active
#              user_timestamp
             }
    }
}   
"""
# sql="user_id > 5", 
zz = sk.SqlMask (table='euro_user',
                   lay=lay, engine=engine)

zz.lay_obj.prop('A.a', 'top-padding', 50)

gtk.main()


