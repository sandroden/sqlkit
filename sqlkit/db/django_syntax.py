"""
Django syntax utilities
=======================

This module provides some functions to allow use of django syntax in filters.
You can look an introduction on lookup filters on `django's site`_
The aim is not at all compatibility with django (that has nothing to do with this
framework) but a way to:

  * make it easy to add filters and constraints
  * make it easy to store queries (that need to store filters and constraints)

These function are used in sqlfilter and in completion beside add_constrint method
of sqlwidget. 

All of these functions act on a mapper becouse it has info on PropertyLoaders. In completion,
the mapper is used to follow the join_path even if the query (a ``sqlalchemy.select``),
will not be issued on a ``session.query`` object

.. _`django's site`: http://docs.djangoproject.com/en/dev/topics/db/queries/#field-lookups-intro

supported lookup
----------------

  :like/ilike: use like operator, ilike if available
  :regexp/iregexp: now ~/~* for postgres and REGEX for mysql like again for the rest
  :lt/gt:  less than / grater than (<, >)
  :lte/gte:  less than equal/ grater than equal(<=, >=)
  :eq/neq:  equal / not equal ( = , !=)
  :in:  IN (argument must be a list)
  :null: IS NULL / IS NOT NULL (depending if arg is True/False)

conjunctions
------------

``django2sqlakchemy`` and ``django2query`` connect all argumnets with AND operator
by default. It's possible to use ``OR`` operator adding ``OR=True``  argument.



"""

from sqlalchemy.sql.expression import ColumnElement, ClauseList 
from sqlalchemy.sql import and_, or_
from sqlalchemy.orm import ColumnProperty, PropertyLoader
from sqlalchemy.types import Date, DateTime
from copy import deepcopy
from dry.dateutils import string2dates

OPERATORS = {
    'like'  : 'like',
    'ilike' : 'ilike',
    'iregexp' : '~*',
    'regexp' : '~',
    'lt'   : '<',
    'gt'   :  '>',
    'lte'  : '<=',
    'gte'  : '>=',
    'eq'   : '=',
    'neq'   : '!=',
    'equal': '=',
    'in'   : 'IN',
    'null' : 'IS NULL',
    }

class DjangoParser(object):
    """
    parses a django-like argument to compose a sqlalchemy
    ColumnList/ColumnElement object to be used in queries
    """
    def __init__(self, mapper=None, query=None, OR=False):
        """
        A sqlalchemy.Table object
        """
        self.mapper = mapper
        self.query = query
        self.OR = OR
        self.expressions = []
        self.joins = []

    def parse(self, kw):
        """
        must be a single condition
        parse a django-like condition
        """
        join_path, op, col, op_str, value = django2components(self.mapper, kw)

        self.joins += [join_path]

        if op_str == 'icontains':
            sql = col.match(value)
        elif op_str == 'null':
            sql = col == value  ## True | False
        elif op_str == 'ilike': # SA manages difference where there is no ILIKE operator
            sql = col.ilike(value)
        elif self.is_date(col):
            start, stop = string2dates(value)
            sql = col.op(op)(start)
        else:
            sql = col.op(op)(value)

        self.expressions += [sql]
            
    def is_date(self, col):

        if isinstance(col.type, (Date, DateTime)):
            return True
        return False
        
    def sql(self):
        if self.OR:
            sql = or_(*self.expressions)
        else:
            sql = and_(*self.expressions)
        return sql

    def compose(self):
        for path in self.joins:
            self.query = self.query.join(path).reset_joinpoint()
        return self.query.filter(self.sql() )

#######  Functions  ############
    
def django2components(mapper, kw):
    """
    Split a single argument/value into a tuple of 5 components:

      :path:    what should be used in a join to reach the column of the expression
      :str_op:  string version of the operator (eg: lte)
      :col:     sqlalchemy column on which the expression will operate 
      :op:      simbolic version of the operator (eg: <=)
      :value:   value of the argument
      
    return: path, str_op, col, op, value
    """
    table = mapper.local_table
    name = kw.keys()[0]
    value = kw[name]
    tokens = name.split('__')
    joins = []
    
    if len(tokens) == 1:  # field_name='abc'
        op_str = 'eq'
        attr = tokens[0]
        col = getattr(table.columns, attr)
        value = kw[attr]

    else:  # data_gte=today() -- address__city__country__in=['Italy','France']
        if tokens[-1] in OPERATORS:
            op_str = tokens.pop()
        else:
            op_str = 'eq'
        attr = tokens.pop()
        if tokens: # may be consumed by now...
            joins = deepcopy(tokens)
            col = get_foreign_column(mapper, path=tokens, attr=attr)
        else:
            col = table.columns[attr]

    op = OPERATORS[op_str]
    if op_str in ('regexp', 'iregexp'):
        op, value = get_regexp_op(mapper.local_table.metadata.bind.name, op_str, value)
    return joins, op, col, op_str, value

def get_foreign_column(mapper, path=None, attr=None):
    """
    follow PropertyLoaders chain to get the last referenced column
    """
    if not mapper:
        raise NotImplementedError("Can't cross relationship if you don't provide a mapper")

    prop = mapper.get_property(path.pop(0))
    for elem in path:
        prop = prop.mapper.get_property(elem)
    return get_column(prop, attr)


def django2query(mapper, query, OR=False, **kw):
    """
    return a new query with new constraints expressed in  'django-style'
    
    """
    parser = DjangoParser(mapper, query, OR=OR)

    for key,val in kw.iteritems():
        parser.parse( {key:val})

    return parser.compose()


def django2sqlalchemy(mapper=None, table=None, OR=False, **kw):
    """
    return a ClauseList and a join path. 
    """
    if table:
        parser = DjangoParser(table=table, query=None, OR=OR)
    else:
        parser = DjangoParser(mapper=mapper, query=None, OR=OR)
        

    for key,val in kw.iteritems():
        parser.parse( {key:val})
    return parser.sql(), parser.joins

def get_column(prop, attr):
    """
    return the column(s?) referenced from a property
    """
    if isinstance(prop, ColumnProperty):
        col = prop.columns[0]
        if col.foreign_keys:  ## FIXME: Should I consider multiple fkey?
            return getattr(col.foreign_keys[0].column.table.c, attr)
        else:
            return prop.columns[0]  ### FIXME: why colums is a list?
    elif isinstance(prop, PropertyLoader):
        return getattr(prop.mapper.local_table.c, attr)  
    
def path2join(path, mapper):
    table = mapper.local_table
    join = table
    for elem in path:
        for token in elem:
            prop = mapper.get_property(token)
            if isinstance(prop, ColumnProperty):
                col = prop.columns[0]
                if col.foreign_keys:  ## FIXME: Should I consider multiple fkey?
                    table = col.foreign_keys[0].column.table
            elif isinstance(prop, PropertyLoader):
                table = prop.remote_side[0].table

            join = join.join(table)

    return join

def get_regexp_op(bind_name, op_str, value):
    """
    return the best approximation to regexp operator
    in sqlite fall back to (I)LIKE
    """
    if bind_name == 'postgres':
        if op_str == 'regexp':
            return '~', value
        else:
            return '~*', value
    elif bind_name == 'mysql':
        return 'REGEXP', value
    else:
        return 'like', '%' + value + '%'
    
    
if __name__ == '__main__':

    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine, engine
    from sqlalchemy.orm import relation, scoped_session, sessionmaker

    
    Base = declarative_base()
    meta = Base.metadata
    meta.bind = create_engine('sqlite://')
#    meta.bind = create_engine('postgres://localhost/c2')
#    meta.bind = create_engine('mysql://localhost/c2')
    Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=meta.bind))
    session = Session()

    class User(Base):
        __tablename__ = 'user'

        id = Column('id', Integer, primary_key=True)
        name = Column('name', String(50))
        addresses = relation("Address", backref="user")

    class Address(Base):
        __tablename__ = 'address'

        id = Column('id', Integer, primary_key=True)
        email = Column('email', String(50))
        user_id = Column('user_id', Integer, ForeignKey('user.id'))
        provider_id = Column('provider_id', Integer, ForeignKey('provider.id'))
        
    class Provider(Base):
        __tablename__ = 'provider'

        id = Column('id', Integer, primary_key=True)
        provider = Column('provider', String(50))
        country_id = Column('country_id', Integer, ForeignKey('country.id'))
        addresses = relation("Address", backref="provider")
        
    class Country(Base):
        __tablename__ = 'country'

        id = Column('id', Integer, primary_key=True)
        provider = Column('country', String(50))
        addresses = relation("Provider", backref="country")
        

    query = session.query(User)
    def test(*args, **kw):
        print django2query(User.__mapper__, query, **kw)

    def test2(*args, **kw):
        sql, join = django2sqlalchemy(User.__mapper__,  **kw)
        print sql, join

#     test(name='ed')
#     test(name='ed', addresses__email__icontains='google')
#     test(name='ed', addresses__provider__provider__icontains='google', OR=True)
    test(name='ed', addresses__provider__country__country__icontains='ita', OR=True)
    test2(name='ed', addresses__email='@me',
          addresses__provider__country__country__icontains='ita', OR=True)
