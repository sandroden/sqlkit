#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import py_path, config, reflect, mask
import sd
sd.dbg = 1

from sqlalchemy import *
from layout import *
from validator import Validator

engine = config.spawnEngine(echo=False)
map_labels(filename='label_map.txt')

lay = """
{h  {-| user_name
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
#        user_timestamp
       }
    }
}   
"""
# sql="user_id > 5", 
zz = mask.SqlMask (table='euro_user',
                   lay=lay, engine=engine)

show_widgets(zz.w['Window'])
gtk.main()


