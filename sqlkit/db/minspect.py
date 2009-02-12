from sqlalchemy import *
import sqlalchemy 
import sys
from sqlkit import debug as dbg
import datetime
import decimal
import re
from  sqlalchemy.orm import properties
import sqlalchemy.orm.properties 
from sqlkit.misc.utils import Container

SA_TYPE_MAP =  {
    sqlalchemy.types.String : str,
    sqlalchemy.types.Unicode : str,
    sqlalchemy.types.Integer  : int,
    sqlalchemy.types.SmallInteger  : int,
    sqlalchemy.types.Float  : float,
    sqlalchemy.types.DateTime  : datetime.datetime,
    sqlalchemy.types.Date  : datetime.date,
    sqlalchemy.types.Interval  : datetime.timedelta,
    sqlalchemy.types.Time  : datetime.time,
    sqlalchemy.types.Numeric : decimal.Decimal,
    sqlalchemy.types.Text  : str, 
    sqlalchemy.types.UnicodeText  : str, 
    sqlalchemy.types.Boolean  : bool, 
    sqlalchemy.types.Binary : str, # ????
    }

PROPERTIES = properties
class MissingPrimaryKeyError(Exception): pass
def is_serial (c):
    if hasattr (c.default, 'arg') and hasattr (c.default.arg, 'text'):
        if "nextval" in c.default.arg.text:
            return True
    else:
        return False


class InspectMapper(Container):
    """inspect a mapper and gather all info on fields normally used.
    Adds attributes for each field_name pointing to a dictionary with:
    
    table_name  (string)
    name        (string)
    table       (sqlalchemy Table obj)
    db_type     (db type)
    type        (python-type) (not yet)
    col_spec    (string) eg: INTEGER, STRING
    is_serial   bool
    length      None or a Number
    property    the property used to access these data
    """
    field_list = None  # list of field_names in the mapper (all possible tables)
    props  = None  # dict of properties 
    pkeys  = None  # dict table:[pkey1,...]

    def __init__(self, mapper, noup=None, ro=False):
        """
        noup: list of fields that will get a rw=False field
        ro:   bool. if True no update/insert/delete will be possible
           """
        global SA_TYPE_MAP
        self.ro = ro
        
        try:
            # these type so no have a correspondence a base in a SA Type
            SA_TYPE_MAP.update({
                sqlalchemy.databases.postgres.PGInet  : str, 
                sqlalchemy.databases.postgres.PGChar  : str, 
                sqlalchemy.databases.postgres.PGInterval  : datetime.timedelta,
                })
        except Exception, e:
            pass

        self.field_list = []
        self.fields = Container()
        self.primarytable = self.get_primary_table
        self.noup = self.parse_noup(noup)
        self.mapper = mapper
        self.props = []
        self.pkeys = {}
        self.table_mappers = {}  # mappers to tables
        self.n = 0
        self.loop_on_props()

                              
    def get_py_type(self, Type,):
        for typ in (Type,) + Type.__bases__:
            try:
                return SA_TYPE_MAP[typ]
            except KeyError:
                continue

        raise NotImplementedError("Couldn't resolve SA type for %s" % Type)
        
        
    def loop_on_props(self):
        """Add field gathering info from the mapper 
        At the mome we only use properties that are 
        """
        props = self.mapper.iterate_properties
        
        for prop in props:
            if isinstance(prop, properties.ColumnProperty):
                self._add_field(prop.key, self.mapper, property=prop)
            elif isinstance(prop, properties.PropertyLoader):
                self._add_loader_field(prop.key, self.mapper, property=prop)
                
    def _add_field(self, field_name, mapper, property=None):
        if field_name in self:
            dbg.write("%s precedentemente definito, cerchi guai..." % field_name)
            return
        
        self.field_list += [ field_name ]
        col = mapper.c[field_name] 
        
        try:
            col_spec = mapper.c[field_name].type.get_col_spec()
        except NotImplementedError,e:
            col_spec = None
        d = Container({
#            'table_name'  :  mapper.local_table.name ,
            'table_name'  :  col.table.name ,
            'name'        :  str(field_name),
            'table'       :  mapper.local_table ,
            'col'         :  mapper.c[field_name] ,
            'db_type'     :  type(mapper.c[field_name].type), 
            'type'        :  self.get_py_type(type(mapper.c[field_name].type), ),
            'col_spec'    :  col_spec,
            'is_serial'   :  is_serial(mapper.c[field_name]),
            'property'    :  property,
            'fkey'        :  False,
            'default'     :  mapper.c[field_name].default,
            'pkey'        :  mapper.c[field_name].primary_key,
            'nullable'    :  mapper.c[field_name].nullable,
            'mapper'      :  mapper,
            'editable'        :  self.set_noup(field_name, col.name, col)
#            'direction'   :  mapper.props[field_name].direction
            })
        try:
            d['length'] = mapper.c[field_name].type.length
        except:
            d['length'] = None

        if col.table.name not in self.table_mappers:
            #dbg.write("%s %s" % (mapper.local_table.name, self.table_mappers))
            self.table_mappers[col.table.name] = (self.mapper.class_, self.mapper)
            self.pkeys[col.table.name] = []

#         if mapper.local_table.name not in self.table_mappers:
#             #dbg.write("%s %s" % (mapper.local_table.name, self.table_mappers))
#             self.table_mappers[mapper.local_table.name] = (mapper.class_, mapper)
#             self.pkeys[mapper.local_table.name] = []

        if d['pkey']:
            #dbg.write("si %s -> %s" % (field_name, mapper.local_table.name ))
            self.pkeys[col.table.name] += [field_name]

        d['fkey'] = mapper.c[field_name].foreign_keys

#         if mapper.c[field_name].foreign_keys:
#              d['fkey'] = (mapper.c[field_name].foreign_key.column.table.name,
#                         mapper.c[field_name].foreign_key.column.name)
        self.fields.add_element(field_name, d)
        #setattr(self.fields, field_name,  d)

    def _add_loader_field(self, field_name, mapper, property=None):
        """
        Add db_specs for a field that correspond to a Loader of a foreign field
        This is the loader of a field in a table connected via an intermediate one or
        via a OneToMany relation

        No real attribute is present in the db table

        SqlMask will use CollectionWidget to represent it and will explicily be asked to
        via a field in the layout
        """

        if field_name in self:
            dbg.write("%s precedentemente definito, cerchi guai..." % field_name)
            return
        
        self.field_list += [ field_name ]

        d = {
            'mapper'  :  property.mapper ,
            'name'        :  str(field_name),
            'table'       :  property.table,
            'table_name'       :  property.table.name,
#            'col'         :  property.mapper.c[field_name] ,
            'db_type'     :  None,   ## FIXME: this is used tor table 
            'type'        :  str,  # FIXME
            'col_spec'    :  None,
            'is_serial'   :  False,
            'property'    :  property,
            'fkey'        :  False,
            'default'     :  None,
            'pkey'        :  None,
            'nullable'    :  True,
#            'mapper'      :  mapper,
            'editable'        :  True,
#            'direction'   :  mapper.props[field_name].direction
            'remote_attr' : [c.name for c in property.remote_side]
            }

        try:
            d['length'] = mapper.c[field_name].type.length
        except:
            d['length'] = None


        table_name = mapper.local_table.name
        if table_name not in self.table_mappers:
            self.table_mappers[table_name] = (mapper.class_, mapper)
            self.pkeys[table_name] = []

        self.fields.add_element(field_name, d)
        #setattr(self.fields, field_name,  d)

    def keys(self):
        """Return all the field_names in the mapper but not loaders
        """
        ret = []
        for m in self.tables(mode='mapper' ):
            ret += m.c.keys()
        return ret

    def all_keys(self):
        """Return all the field_names in the mapper comprising loaders
        """
        ret = []
        for prop in self.mapper.iterate_properties:
            ret += [prop.key]
        return ret

    def __iter__(self):
        return self

    def __contains__(self, item):
        if item in self.field_list:
            return True
        return False

    def __getitem__(self, item):
        #print "item", item, type(item)
        return getattr(self, str(item))
    
    def __len__(self):
        return len(self.field_list)
    
    def tables(self, mode='name'):
        """return the table_names of the tables in the mapper
        if mode='mapper', returns the mappers
        the main table will be in position '0'
        """
        #dbg.write(self.table_mappers)
        if mode == 'name':
            first_table = self.mapper.local_table.name 
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
        return [f for f in self.field_list if self[f]['table_name'] == table_name ]
    
    def prop_fields(self, table_name):
        """list of all field_names in 'table' linked as propperty prop"""
        table_name = [p[2] for p in self.props if p[0] == table_name][0]
        return self.table_fields(table_name)
    
    def get_mapper(self, table_name):
        """return the mapper of that table"""
        dbg.write('table_mappers', self.table_mappers)
        return self.table_mappers[table_name][1]
    
#     def mapper(self, table_name):
#         """return the mapper of that table"""
#         return self.table_mappers[table_name][1]
    
    def get_class(self, table_name):
        """return the class of that table"""
        return self.table_mappers[table_name][0]
    
    def get_pkeys(self, table_name):
        """return the list of the pkeys for that table"""
        try:
            return self.pkeys[table_name]
        except KeyError:
            raise MissingPrimaryKeyError("%s does not seem to have a PKey" %
                                         table_name)
        
    def parse_noup(self, noup):
        """parse noup to set fields that are not updateable
        """
        if noup == None:
            return []
        if isinstance(noup, str):
            noup = re.split('[ ,]+', noup)
        return noup
        
    def set_noup(self, field_name, table_name, col):
        if self.ro:
            return False
        
        editable = True
        ## if this field is not in the main (primary) table, don't editable it
#         if table_name != self.primarytable():
#             #dbg.write("%s: %s != %s" % (field_name, table_name, self.primarytable()))
#             editable = False

        if field_name in self.noup:
            #dbg.write("2", field_name, 'noup')
            editable = False
            
        return editable
        
    def get_join_cnd(self):
        tables = self.tables(mode='mapper')
        return get_join_cnd(tables)

    def get_primary_table(self, name=True):
        primarytable = self.mapper.local_table
        while isinstance(primarytable, sqlalchemy.sql.Join):
            primarytable = primarytable.left
        if name:
            return primarytable.name
        else:
            return primarytable

    def next(self):
        """returns the next item in the data set,
        or tells Python to stop"""
        if self.n is None:
            self.n = -1
          
        try:
            self.n += 1
            r = getattr(self, self.field_list[self.n])
        except:
            raise StopIteration
      
        if not r:
            raise StopIteration
        return r

    def __str__(self):
        return "InspectMapper for keys: %s" % self.keys()
        
    def __repr__(self):
        return "<InspectMapper for keys: %s>" % self.keys()

def get_foreign_info(ForeignKey, names=True):

    foreign_keys = ForeignKey

    if len(foreign_keys) > 1:
        raise UnhandledMultipleForeignkeys(foreign_keys)
    else:
        fkcol = foreign_keys[0]
        ## table/column name are unicode but they must be strng to be
        ##     used as key in dicts
        if names:
            return (str(fkcol.column.table.name), str(fkcol.column.name))
        else:
            return (fkcol.column.table, fkcol.column)
    
# def get_join_cnd(tables, mode='sa'):
#     """return a join condition of the sqlobj.Tables in tables
#     mode: sa (sqlalchemy objects) or 'str' (string)
#     """
#     #dbg.show_caller()
#     #dbg.write()
#     if len(tables) == 1:
#         return []
#     cnd = []
#     #dbg.write("tables:", tables)
# #    tbls = [col.table for col in t.c for t in tables]

#     tbls = {}  # which tables are used in these table that can really be joins
#     for t in tables:
#         dbg.write(t, type(t))
#         for col in t.c:
#             tbls[col.table] = col.table.name
#     #dbg.write(tbls.values())



#     for t in tables:
#         #dbg.write(t)
#         for col in t.c:
#             fkey = col.foreign_keys
#             if fkey and fkey.column.table in tbls:
#                 #dbg.write("col:", col, " -- fk:", col.foreign_key.column)
#                 cnd += [ col == fkey.column ]
#                 cnd_str = "%s.%s = %s.%s" % (col.table.name, col.name,
#                                              fkey.column.table.name,
#                                              fkey.column.name)
#                 #dbg.write(cnd_str)
#     if mode == 'sa':
#         return cnd
#     else:
#         return cnd_str


# def list_tables(eng=None, schema=None):
#     if not eng:
#         eng = schema.default_metadata.engine

#     if eng.name == 'sqlite':
#         sql = """
#         SELECT name FROM sqlite_master
#         WHERE type='table'
#         ORDER BY name;"""
#     elif eng.name == 'postgres':
#         if schema == None:
#             schema_constraint = ''
#         else:
#             schema_constraint = "AND n.nspname = :schema"
#         sql = """
#            SELECT c.relname as name, 
#              n.nspname as schema,c.relkind,
#              u.usename as owner
#            FROM pg_catalog.pg_class c
#                 LEFT JOIN pg_catalog.pg_user u ON u.usesysid = c.relowner
#                 LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
#            WHERE c.relkind IN ('r')
#                  %s
#                  AND pg_catalog.pg_table_is_visible(c.oid)
#            ORDER BY 1,2;
#            """ % (schema_constraint)
#         # sequences and views can be found in postgres just changind this:
#         # c.relkind IN ('r') 'v','S'
#     elif eng.name in ( 'mysql'):
#         sql = "SHOW TABLES"
        
#     ret = eng.text(sql).execute(schema=schema)
#     tables = [R[0] for R in ret]
#     return tables





        
#     def get(self, record, field_name, n=0):
#         at = getattr(self, field_name)
#         if not at['property']:
#             return getattr(record, field_name)
#         else:
#             print at['property'], type(at['property'])
#             data = getattr(record, at['property'][0])
#             return getattr(data, field_name)

# class InspectJoinMapper(InspectMapper):
#     def _add_field_(self, col):
#         if col.key in self:
#             dbg.write("%s precedentemente definito, cerchi guai..." % col.key)
#             return
        
#         self.field_list += [ col.key ]
#         d = {
#             'table_name'  :  col.table.name ,
#             'name'        :  col.name,
#             'table'       :  col.table ,
#             'col'         :  col,
#             'db_type'     :  type(col.type), 
#             'type'        :  self.pytype[type(col.type)],
#             'col_spec'    :  col.type.get_col_spec(),
#             'is_serial'   :  is_serial(col),
#             'property'    :  '',   # no property for a join
#             'fkey'        :  False,
#             'pkey'        :  col.primary_key,
#             'nullable'    :  col.nullable,
#             'mapper'      :  self.mapper,
#             'editable'        :  self.set_noup(col.key, col.table.name, col)
# #            'direction'   :  mapper.props[field_name].direction
#             }
#         try:
#             d['length'] = col.type.length
#         except:
#             d['length'] = None

#         if col.table.name not in self.table_mappers:
#             #dbg.write("%s %s" % (mapper.local_table.name, self.table_mappers))
#             self.table_mappers[col.table.name] = (self.mapper.class_, self.mapper)
#             self.pkeys[col.table.name] = []

#         if d['pkey']:
#             #dbg.write("si %s -> %s" % (field_name, mapper.local_table.name ))
#             self.pkeys[col.table.name] += [col.name]

#         if col.foreign_key:
#              d['fkey'] = (col.foreign_key.column.table.name,
#                         col.foreign_key.column.name)
#         setattr(self, col.name,  d)
    
#     def get_primary_table(self):
#         #dbg.show_caller()
#         primarytable = self.mapper.local_table
#         while isinstance(primarytable, sqlalchemy.sql.Join):
#             primarytable = primarytable.left
#         table = primarytable.name
#         return table
#         #dbg.write('primarytable', table)




