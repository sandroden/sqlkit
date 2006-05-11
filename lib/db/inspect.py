from sqlalchemy import *
import sys, dbg
import datetime

class MissingPrimaryKeyError(Exception): pass
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
            dbg.write("no pg types")
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
            dbg.write("no sa types")
            pass
                              

        self.fields = []
        self.mapper = mapper
        self.props = []
        self.pkeys = {}
        self.table_mappers = {}  # mappers to tables
        self.n = 0
        self.loop_on_props()
    
    def loop_on_props(self):
        for prop in self.mapper.props:
            attr = self.mapper.props[prop]
            ## here we populate props
            if isinstance(attr, mapping.properties.LazyLoader) or \
               isinstance(attr, mapping.properties.EagerLoader):
                #self.props[prop] = attr.target.name  # the table reached thru 'prop'
                m = attr.mapper
                self.props += [(prop, attr.direction, m.table.name)]
                for field_name in m.c.keys():
                    self._add_field(field_name, m, prop)
            else:
                self._add_field(prop, self.mapper)

    def _add_field(self, field_name, mapper, property=None):
        if field_name in self:
            dbg.write("%s precedentemente definito, cerchi guai..." % field_name)
            return
        
        self.fields += [ field_name ]
        d = {
            'table_name'  :  mapper.table.name ,
            'name'        :  field_name,
            'table'       :  mapper.table ,
            'col'         :  mapper.c[field_name] ,
            'pg_type'     :  type(mapper.c[field_name].type), 
            'type'        :  self.pytype[type(mapper.c[field_name].type)],
            'col_spec'    :  mapper.c[field_name].type.get_col_spec(),
            'is_serial'   :  is_serial(mapper.c[field_name]),
            'property'    :  property,
            'fkey'        :  False,
            'pkey'        :  mapper.c[field_name].primary_key,
            'nullable'    :  mapper.c[field_name].nullable,
            'mapper'      :  mapper,
#            'direction'   :  mapper.props[field_name].direction
            }
        try:
            d['length'] = mapper.c[field_name].type.length
        except:
            d['length'] = None

        if mapper.table.name not in self.table_mappers:
            #dbg.write("%s %s" % (mapper.table.name, self.table_mappers))
            self.table_mappers[mapper.table.name] = (mapper.class_, mapper)
            self.pkeys[mapper.table.name] = []

        if d['pkey']:
            #dbg.write("si %s -> %s" % (field_name, mapper.table.name ))
            self.pkeys[mapper.table.name] += [field_name]

        if mapper.c[field_name].foreign_key:
             d['fkey'] = (mapper.c[field_name].foreign_key.column.table.name,
                        mapper.c[field_name].foreign_key.column.name)
        setattr(self, field_name,  d)

    def keys(self):
        """Return all the field_names in the mapper
        """
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
        the main table will be in position '0'
        """
        #dbg.write(self.table_mappers)
        if mode == 'name':
            first_table = self.mapper.table.name 
            ret = [t for t in self.table_mappers.keys() if t != first_table ]
            return [ first_table ] + ret
            #dbg.write(self.table_mappers.keys())
            #return self.table_mappers.keys()
        else:
            first_mapper = self.mapper
            ret = [t[1] for t in self.table_mappers.values()
                   if t[1] != first_mapper]
            #dbg.write([t[1] for t in self.table_mappers.values()])
            return [ first_mapper ] + ret
            
    def table_fields(self, table_name):
        """list of all field_names in 'table' """
        return [f for f in self.fields if self[f]['table_name'] == table_name ]
    
    def prop_fields(self, table_name):
        """list of all field_names in 'table' linked as propperty prop"""
        table_name = [p[2] for p in self.props if p[0] == table_name][0]
        return self.table_fields(table_name)
    
    def get_mapper(self, table_name):
        """return the mapper of that table"""
        return self.table_mappers[table_name][1]
    
#     def mapper(self, table_name):
#         """return the mapper of that table"""
#         return self.table_mappers[table_name][1]
    
    def get_class(self, table_name):
        """return the class of that table"""
        return self.table_mappers[table_name][0]
    
    def pkeys(self, table_name):
        """return the list of the pkeys for that table"""
        try:
            return self.pkeys[table_name]
        except KeyError:
            raise MissingPrimaryKeyError("%s does not seem to have a PKey" %
                                         table_name)
        
    def get_join_cnd(self):
        tables = self.tables(mode='mapper')
        return get_join_cnd(tables)

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
        
#     def get(self, record, field_name, n=0):
#         at = getattr(self, field_name)
#         if not at['property']:
#             return getattr(record, field_name)
#         else:
#             print at['property'], type(at['property'])
#             data = getattr(record, at['property'][0])
#             return getattr(data, field_name)

class InspectJoinMapper(InspectMapper):
    def loop_on_props(self):
        for prop in self.mapper.props:
            attr = self.mapper.props[prop]
            for col in attr.columns:
                self._add_field(col)
            
    def _add_field(self, col):
        if col.key in self:
            dbg.write("%s precedentemente definito, cerchi guai..." % col.key)
            return
        
        self.fields += [ col.key ]
        d = {
            'table_name'  :  col.table.name ,
            'name'        :  col.name,
            'table'       :  col.table ,
            'col'         :  col,
            'pg_type'     :  type(col.type), 
            'type'        :  self.pytype[type(col.type)],
            'col_spec'    :  col.type.get_col_spec(),
            'is_serial'   :  is_serial(col),
            'property'    :  '',   # no property for a join
            'fkey'        :  False,
            'pkey'        :  col.primary_key,
            'nullable'    :  col.nullable,
            'mapper'      :  self.mapper,
#            'direction'   :  mapper.props[field_name].direction
            }
        try:
            d['length'] = col.type.length
        except:
            d['length'] = None

        if col.table.name not in self.table_mappers:
            #dbg.write("%s %s" % (mapper.table.name, self.table_mappers))
            self.table_mappers[col.table.name] = (self.mapper.class_, self.mapper)
            self.pkeys[col.table.name] = []

        if d['pkey']:
            #dbg.write("si %s -> %s" % (field_name, mapper.table.name ))
            self.pkeys[col.table.name] += [col.name]

        if col.foreign_key:
             d['fkey'] = (col.foreign_key.column.table.name,
                        col.foreign_key.column.name)
        setattr(self, col.name,  d)
    
    def get_primary_table(self):
        primarytable = self.mapper.primarytable
        while isinstance(primarytable, sqlalchemy.sql.Join):
            primarytable = primarytable.left
        table = primarytable.name
        dbg.write('primarytable', table)
            
def get_join_cnd(tables):
    if len(tables) == 1:
        return []
    cnd = []
    #dbg.write("tables:", tables)
#    tbls = [col.table for col in t.c for t in tables]

    tbls = {}  # which tables are used in these table that can really be joins
    for t in tables:
        for col in t.c:
            tbls[col.table] = col.table.name
    #dbg.write(tbls.values())



    for t in tables:
        #dbg.write(t)
        for col in t.c:
            if col.foreign_key and col.foreign_key.column.table in tbls:
                #dbg.write("col:", col, " -- fk:", col.foreign_key.column)
                cnd += [ col == col.foreign_key.column ]
                #dbg.write(cnd)
    return cnd

def get_props(mapper):
    props = []
    for prop in mapper.props:
        attr = mapper.props[prop]
        if isinstance(attr, sqlalchemy.mapping.properties.LazyLoader) or \
           isinstance(attr, sqlalchemy.mapping.properties.EagerLoader):
            props += [(prop, attr.direction)]
    return props
    


