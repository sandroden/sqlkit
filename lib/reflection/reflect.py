
from sqlalchemy import *
import sys, sd
import datetime

# class Mapper (object):
#     pass

# def mapTable (engine, table_name):
#     return Table (table_name, engine, autoload = True)

# def getMapper (table):
#     return mapper (Mapper, table)

# def getRecord (mapper, **kwds):
#     return mapper.get_by (**kwds)

def is_serial (c):
    if hasattr (c.default, 'arg') and hasattr (c.default.arg, 'text'):
        if "nextval" in c.default.arg.text:
            return True
    else:
        return False


class InspectMapper(dict):
    """inspect a mapper and gather all info on fields normally used.
    Adds attributes for each field_name pointing to a dictionary with:
    
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
    fields = None  # list of field_names in the mapper (all possible tables)
    props  = None  # dict of properties 
    pkeys  = None  # dict table:[pkey1,...]

    def __init__(self, mapper, noup=None, mode='rw'):
        """noup: list of fields that will get a rw=False field
           mode: rw|ro if mode=ro no update/insert/delete will be possible
           """
        self.pytype = {}
        ## used by postgresql
        try:
            self.pytype.update({
                sqlalchemy.databases.postgres.PGString : str,
                sqlalchemy.databases.postgres.PGInteger  : int,
                sqlalchemy.databases.postgres.PGFloat  : float,
                sqlalchemy.databases.postgres.PG2DateTime  : datetime.datetime,
                sqlalchemy.databases.postgres.PG2Date  : datetime.date,
                sqlalchemy.databases.postgres.PGChar  : str, 
                sqlalchemy.databases.postgres.PGString  :  str, 
                sqlalchemy.databases.postgres.PGBoolean  : bool, 
                })
        except:
            sd.debug("no pg types")
            pass
                              
        ## used by sqlite
        try:
            self.pytype.update({
                sqlalchemy.types.String : str,
                sqlalchemy.types.Integer  : int,
                sqlalchemy.types.Float  : float,
                sqlalchemy.types.DateTime  : datetime.datetime,
                sqlalchemy.types.Date  : datetime.date,
#                sqlalchemy.types.Char  : str, 
                sqlalchemy.types.String  :  str, 
                sqlalchemy.types.Boolean  : bool, 
                })
        except:
            sd.debug("no sa types")
            pass
                              

        self.fields = []
        self.props = []
        self.pkeys = {}
        self.table_mappers = []  # mappers to tables
        self.n = 0
        for prop in mapper.props:
            attr = mapper.props[prop]
            ## here we populate props
            if isinstance(attr, sqlalchemy.mapping.properties.LazyLoader) or \
               isinstance(attr, sqlalchemy.mapping.properties.EagerLoader):
                #self.props[prop] = attr.target.name  # the table reached thru 'prop'
                self.props += [(prop, attr.direction)]
                m = attr.mapper
                for field_name in m.c.keys():
                    self._add_field(field_name, m, prop)
            else:
                self._add_field(prop, mapper)

    def _add_field(self, field_name, mapper, property=None):
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
            'fkey'        :  False,
            'pkey'        :  mapper.c[field_name].primary_key,
#            'direction'   :  mapper.props[field_name].direction
            #'label'  :   ,
            #'widget'  :   ,
            }
        try:
            d['length'] = mapper.c[field_name].type.length
        except:
            d['length'] = None

        if (mapper.table.name, mapper) not in self.table_mappers:
            #sd.debug("%s %s" % (mapper.table.name, self.table_mappers))
            self.table_mappers += [(mapper.table.name, mapper)]
            self.pkeys[mapper.table.name] = []

        if d['pkey']:
            #sd.debug("si %s -> %s" % (field_name, mapper.table.name ))
            self.pkeys[mapper.table.name] += [field_name]

        if mapper.c[field_name].foreign_key:
             d['fk'] = (mapper.c[field_name].foreign_key.column.table.name,
                        mapper.c[field_name].foreign_key.column.name)
        setattr(self, field_name,  d)

    def keys(self):
        ret = []
        for m in self.tables(mode='mapper' ):
            ret += m.c.keys()
        return ret

    def __iter__(self):
        return self

    def __contains__(self, item):
        if item in self.fields:
            return True
        return False

    def __getitem__(self, item):
        return getattr(self, item)

    def __len__(self):
        return len(self.fields)
    
    def tables(self, mode='name'):
        """return the table_names of the tables in the mapper
        if mode='mapper', returns the mappers
        """
        #sd.debug(self.table_mappers)
        if mode == 'name':
            return [t[0] for t in self.table_mappers]
        else:
            return [t[1] for t in self.table_mappers]
            
    def table_fields(self, table_name):
        """list of all filed_names in 'table' """
        return [f for f in self.fields if self[f]['table_name'] == table_name ]
    
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

    def __str__(self):
        return "InspectMapper for keys: %s" % self.keys()
        
    def get(self, record, field_name, n=0):
        at = getattr(self, field_name)
        if not at['property']:
            return getattr(record, field_name)
        else:
            print at['property'], type(at['property'])
            data = getattr(record, at['property'][0])
            return getattr(data, field_name)


            
def get_props(mapper):
    props = []
    for prop in mapper.props:
        attr = mapper.props[prop]
        if isinstance(attr, sqlalchemy.mapping.properties.LazyLoader) or \
           isinstance(attr, sqlalchemy.mapping.properties.EagerLoader):
            props += [(prop, attr.direction)]
    return props
    
