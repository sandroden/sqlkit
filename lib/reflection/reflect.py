
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


class Inspect(object):
    def __init__(self, mapper):
        for prop in mapper.props:
            attr = mapper.props[prop] 
            if isinstance(attr, sqlalchemy.mapping.properties.LazyLoader):
                m = attr.mapper
                for c in m.c.keys():
                    # m.c[c].columns
                    # m.c[c]
                    m.c[c]
                    print m.table, c, m.c[c].type
            else:
                # mapper.c[attr.key].columns
                # mapper.c[attr.key]
                c = attr.key
                m = mapper 
                print m.table, c, m.c[c].type


