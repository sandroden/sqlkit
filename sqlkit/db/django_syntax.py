# Copyright (C) 2008, Sandro Dentella <sandro@e-den.it>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Django syntax utilities
=======================

This module provides some functions to allow use of django syntax in filters.
You can look an introduction on lookup filters on `django's site`_
The aim is not at all compatibility with django (that has nothing to do with this
framework) but a way to:

  * make it easy to add filters and constraints
  * make it easy to store queries (that need to store filters and constraints)

These function are used in sqlfilter and in completion beside ``.add_constraint(...)``
method of sqlwidget. 

You never *need* to use these functions. If you prefere you can changed the query
directly with SQLAlchemy syntax, and surely there are situations where that's
necesssary, nevertheless there are situations where this syntax allows to obtain the
same result in less and more readeable code, probably just one line.

All of these functions act on a mapper becouse it has info on PropertyLoaders. In completion,
the mapper is used to follow the *join_path* even if the query (a ``sqlalchemy.select``),
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

``django2sqlakchemy`` and ``django2query`` connect all arguments with AND operator
by default. It's possible to use ``OR`` operator adding ``OR=True``  argument.



"""

from sqlalchemy.sql.expression import ColumnElement, ClauseList 
from sqlalchemy.sql import and_, or_
from sqlalchemy import Table
from sqlalchemy.orm import ColumnProperty, PropertyLoader
from sqlalchemy.types import Date, DateTime
from copy import deepcopy
from sqlkit.misc.datetools import string2dates

OPERATORS = {
    'icontains'  : 'icontains',
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
    def __init__(self, mapper_or_table=None, query=None, OR=False):
        """
        A sqlalchemy.Table object
        """
        if isinstance(mapper_or_table, Table):
            self.mapper = None
            self.table = mapper_or_table
        else:
            self.mapper = mapper_or_table
            self.table = self.mapper.local_table

        self.query = query
        self.OR = OR
        self.expressions = []
        self.joins = []

    def parse(self, kw):
        """
        must be a single condition
        parse a django-like condition
        """
        if self.mapper:
            join_path, op, op_str, value, col = django2components(self.mapper, kw=kw)
        else:
            join_path, op, op_str, value, col = django2components(self.table, kw=kw)
            
        self.joins += [join_path]

        if op_str == 'icontains':
            eng_name = self.table.metadata.bind.name
            if eng_name  == 'sqlite':
                sql = col.ilike("%%%s%%" % value.strip('%'))
            elif eng_name == 'postgres':
                sql = col.op('~*')(value)
            elif eng_name == 'mysql':
                sql = col.op('REGEXP')(value)
                
        elif op_str == 'null':
            sql = col == value  ## True | False
        elif op_str == 'ilike': # SA manages difference where there is no ILIKE operator
            sql = col.ilike(value)
        elif self.is_date(col):
            start, stop = string2dates(value)
            if stop:
                sql = col.op('>=')(start)  &  col.op('<=')(stop)
            else:
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
            if path:
                self.query = self.query.join(*path).reset_joinpoint()

        return self.query.filter(self.sql() )

#######  Functions  ############
    
def django2components(mapper_or_table, kw=None):
    """
    Split a single argument/value into a tuple of 5 components:

      :path:    what should be used in a join to reach the column of the expression
      :str_op:  string version of the operator (eg: lte)
      :col:     sqlalchemy column on which the expression will operate 
      :op:      simbolic version of the operator (eg: <=)
      :value:   value of the argument
      
    return: path, str_op, col, op, value
    """
    if isinstance(mapper_or_table, Table):
        mapper = None
        table = mapper_or_table
    else:
        mapper = mapper_or_table
        table = mapper.local_table
        
    name = kw.keys()[0]
    value = kw[name]
    tokens = name.split('__')
    joins = []
    
    if len(tokens) == 1:  # field_name='abc'
        op_str = 'eq'
        attr = tokens[0]
        try:
            col = getattr(table.columns, attr)
        except AttributeError, e:
            col = getattr(mapper.c, attr)
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
            try:
                col = getattr(table.columns, attr)
            except AttributeError, e:
                col = getattr(mapper.c, attr)
            #col = table.columns[attr]

    op = OPERATORS[op_str]
    if op_str in ('regexp', 'iregexp'):
        op, value = get_regexp_op(table.metadata.bind.name, op_str, value)
    return joins, op, op_str, value, col

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
        parser = DjangoParser(table, query=None, OR=OR)
    else:
        parser = DjangoParser(mapper, query=None, OR=OR)

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
    

