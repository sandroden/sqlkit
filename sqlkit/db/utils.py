"""
Utilities
=========

Descr
-----
This module provide a bare simple Class to help creating 
__str__ and __repr__ for tables, using _sqlkit_table.format field


tables
------

tables dictionary is a place where sqlkit looks for search_field and
format for tables (see: ref:`sqlkit_model`).

You can set values directly using TableDescr class or implicitely via
database editing (``sqledit -c url``)
"""
import re
from sqlalchemy import Table

########   descriptor
from layout.utils import Container

class MissingMetadata(Exception): pass

class Descr(object):
    """
    Simple class that provide default __init__ and __str__ to be
    mixed when building classes with declarative layer

    __str__ will use 'format' description from database _sqlkit_fields
    """
    def __init__(self, **kw):
        for key, val in kw.iteritems():
            setattr(self, key, val)
    
    def __str__(self):
        from sqlkit.db.utils import tables
        
        if not self.__tablename__ in tables:
            format = get_description(self.__table__, attr='format')

        return tables[self.__tablename__].format % vars(self)

    __repr__ = __str__
    
class Tables(Container):
    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            try:
                table = TableDescr(key, metadata=db.metadata)
                return table
            except Exception, e:
                raise MissingMetadata("No metadata defined in sqlkit.db.utils")
            

tables = Tables()

class TableDescr(object):
    """
    Format may be eather a normal python format string
    (eg.: "%(title)s - %(year)s")
    in which case each prenthesized token must be a field_name
    or a simple string that again must be a field_name
    'table' may be a string or a sqlalchemy.Table object

    Metadata is not necessary to pick primary key or when autoloading is
    required unless a Table object is given

    Format string passed via TableDescr take precedence over format string
    present in the database (dbformat).

    self.format is always a proper format string
    self.attrs comprises pkey so that can be used for completion
    self.search: this is the field that will be searched for in a foreign
    key context
    """
    pattern = '%\((\w+)\)'
    def __init__(self, table, format=None, pk=None, metadata=None):
        global tables

        if isinstance(table , Table):
            table_name = table.name
            self.table = table
        else:
            table_name = table
            
        self.table_name = table_name
        self.format = format
        self.metadata = metadata
        
        tables[table_name] = self

        self.description = self.guess_description()

        if format:
            self.set_format(format)
        else:
            self.set_format(self.description)

        ## I want self attr to have pkey, that's handy for completion
        if not pk:
            self.add_pk()
        else:
            if pk not in self.attrs:
                self.attrs.insert(0, pk)

    def get_attrs_from_format(self, format):
        """
        Used when format is 
        """
        m = re.findall(self.pattern, format)
        if m:
            return m
        else:
            return [format]
        
    def set_format(self, format):
        m = re.findall(self.pattern, format)
        ## self.attrs is use to get the minimum possible info when completing
        if m:
            self.attrs = m
        else:
            self.attrs = [format]
            self.format = "%%(%s)s" % format
            self.search = format

    def add_pk(self):

        table = self.get_table()
        pkeys = table.primary_key.columns

        for field in pkeys:
            if field.name not in self.attrs:
                self.attrs.insert(0, field.name)
                
    def get_table(self):
        try:
            return self.table
        except AttributeError:
            if not self.metadata:
                raise MissingMetadata("Description  for %s cannot be guessed")
        
        ## first time we meet this table  -> inspect w/ autoload
        return Table(self.table_name, self.metadata, autoload=True)

        

    def guess_description(self):
        """look if a description field is defined, if not use introspection
        return the description field if mode == return otherwise call set_fromat

        """
        table = self.get_table()
        descr_exists = False
        for field_name in table.c.keys():
            if re.search("string|text|char", table.c[field_name].type.__class__.__name__, re.I):
                found_field = field_name
                break

        return field_name
        
    def __str__(self):
        return "table: %s - description: %s\n    format: %s" % (self.table_name, self.description,
                                                            self.format)

    def __repr__(self):
        return "table: %s - format: %s" % (self.table_name, self.format)

def get_description(table, metadata=None, attr='attrs'):
    if isinstance(table, Table):
        table_name = table.name
    else:
        table_name = table
        
    try:
        return getattr(tables[table_name], attr)
    except MissingMetadata, e:
        if isinstance(table, Table):
            return getattr(TableDescr(table), attr)
        return getattr(TableDescr(table_name, metadata=metadata), attr)
    
                      


###################

if __name__ == '__main__':
    from sqlkit.db import proxy

    db = proxy.DbProxy(engine="sqlite://///misc/src/hg/py/sqlkit4/doc/db/movies.sqlite")
    movie = Table('movie', metadata=db.metadata, autoload=True)

    #t = TableDescr('movie', '%(dirctor_id)s - (%(nation)s)', metadata=db.metadata)

    tables['movie'].attrs
    print get_description(movie, attr='format')
    print tables.movie
    print get_description('movie', metadata=db.metadata)
    print get_description('movie', metadata=db.metadata, attr='format')    


