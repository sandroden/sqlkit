
from sqlalchemy import *


class Mapper (object):
  pass

def mapTable (engine, table_name):
  return Table (table_name, engine, autoload = True)

def getMapper (table):
  return mapper (Mapper, table)

def getRecord (mapper, **kwds):
  return mapper.get_by (**kwds)

def is_serial (c):
  if hasattr (c.default, 'arg') and hasattr (c.default.arg, 'text'):
    if "nextval" in c.default.arg.text:
      return True
  else:
    return False

