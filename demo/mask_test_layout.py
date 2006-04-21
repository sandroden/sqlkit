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
{h  {-| L=user_name e=user_name
      L=user_last_name e=user_last_name
    }
    {
       {-|>>.archivio
#         L=user_birth_date d=user_birth_date
         user_sex
         user_age
         city_id

       }
       {-|>.stato
         L=user_active c=user_active
#        L=user_timestamp d=user_timestamp
       }
    }
}   
"""

zz = mask.SqlMask (sql="user_id > 5", table='euro_user',
                   lay=lay, engine=engine)

gtk.main()


