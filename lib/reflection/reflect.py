
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


class InspectMapper(object):
    """inspect a mapper and gather all info on fields normally used. Adds attributes
    for each field_name pointing to a dictionary with:
    table_name  (string)
    name        (string)
    table       (sqlalchemy Table obj)
    pg_type     (pg type)
    type        (python-type) (not yet)
    col_spec    (string) eg: INTEGER, STRING
    is_serial   bool
    length      None or a Number
    property    the property used to access these data
    """
    def __init__(self, mapper):
        import datetime
        self.pytype = {
            sqlalchemy.databases.postgres.PGString : str,
            sqlalchemy.databases.postgres.PGInteger  : int,
            sqlalchemy.databases.postgres.PG2DateTime  : datetime.datetime,
            sqlalchemy.databases.postgres.PG2Date  : datetime.date,
            sqlalchemy.databases.postgres.PGChar  : str, 
            sqlalchemy.databases.postgres.PGString  :  str, 
            sqlalchemy.databases.postgres.PGBoolean  : bool, 
        }

        self.fields = []
        self.n = None
        for prop in mapper.props:
            attr = mapper.props[prop] 
            if isinstance(attr, sqlalchemy.mapping.properties.LazyLoader):
                m = attr.mapper
                for field_name in m.c.keys():
                    self.add_field(field_name, m, prop)
            else:
                self.add_field(prop, mapper)

    def add_field(self, field_name, mapper, property=None):
        self.fields += [ field_name ]
        d = {
            'table_name'  :  mapper.table.name ,
            'name'        :  field_name,
            'table'       :  mapper.table ,
            'pg_type'     :  type(mapper.c[field_name].type), 
            'type'        :  self.pytype[type(mapper.c[field_name].type)],
            'col_spec'    :  mapper.c[field_name].type.get_col_spec(),
            'is_serial'   :  is_serial(mapper.c[field_name]),
            'property'    :  property,
            #'label'  :   ,
            #'widget'  :   ,
            }
        try:
            d['length'] = mapper.c[field_name].type.length
        except:
            d['length'] = None


        setattr(self, field_name,  d)

    def keys(self):
        return self.fields

    def __iter__(self):
        return self

    def __contains__(self, item):
        if item in self.fields:
            return True
        return False

    def __getitem__(self, item):
        return self[self.fields[self.n]]

    def __len__(self):
        return len(self.fields)
        
    def next(self):
        """returns the next item in the data set,
        or tells Python to stop"""
        if self.n is None:
            self.n = -1
            
        try:
            self.n += 1
            r = getattr(self, self.fields[self.n])
        except:
            raise StopIteration
        
        if not r:
            raise StopIteration
        return r

    def get(self, record, field_name, n=0):
        at = getattr(self, field_name)
        if not at['property']:
            return getattr(record, field_name)
        else:
            print at['property'], type(at['property'])
            data = getattr(record, at['property'][0])
            return getattr(data, field_name)


            
