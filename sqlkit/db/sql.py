from sqlalchemy.sql.expression import ColumnElement, ClauseList 
from sqlalchemy.sql import and_, or_
from sqlalchemy.orm import ColumnProperty, PropertyLoader
from copy import deepcopy

OPERATORS = {
    'like'  : 'like',
    'ilike' : 'ilike',
    'icontains' : '~*',
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
    }

class DjangoParser(object):
    """
    parses a django-like command line to compose a sqlalchemy
    ColumnList/ColumnElement object to be used in squeries
    """
    def __init__(self, mapper, query, or_=False):
        """
        A sqlalchemy.Table object
        """
        self.mapper = mapper
        self.table = mapper.local_table
        self.query = query
        self.or_ = or_
        self.bind = self.table.metadata.bind
        self.expressions = []
        self.joins = []

    def parse(self, kw):
        """
        must be a single condition
        parse a django-like condition
        """
        name = kw.keys()[0]
        value = kw[name]
        tokens = name.split('__')

        if len(tokens) == 1:  # field_name='abc'
            op = 'eq'
            attr = tokens[0]
            col = getattr(self.table.columns, attr)
            value = kw[attr]
            
        else:  # data_gte=today() -- address__city__country__in=['Italy','France']
            if tokens[-1] in OPERATORS:
                op = tokens.pop()
            else:
                op = 'eq'
            attr = tokens.pop()
            if tokens: # may be consumed by now...
                self.joins += [deepcopy(tokens)]
                col = self.get_foreign_column(path=tokens, attr=attr)
            else:
                col = self.table.columns[attr]

        OP = OPERATORS[op]
        if op == 'icontains':
            sql = col.match(value)
        else:
            sql = col.op(OP)(value)
            
        self.expressions += [sql]
            
    def get_foreign_column(self, path=None, attr=None):
        """
        follow PropertyLoaders chain to get the last referenced column
        """

        prop = self.mapper.get_property(path.pop(0))
        for elem in path:
            prop = prop.mapper.get_property(elem)
        if isinstance(prop, ColumnProperty):
            return prop.columns[0]  ### FIXME: why colums is a list?
        elif isinstance(prop, PropertyLoader):
            return getattr(prop.mapper.local_table.c, attr)  ### FIXME: why colums is a list?

    def sql(self):
        if self.or_:
            sql = or_(*self.expressions)
        else:
            sql = and_(*self.expressions)
        return sql

    def compose(self):
        for path in self.joins:
            self.query = self.query.join(path).reset_joinpoint()
        return self.query.filter(self.sql() )

def django2query(mapper, query, or_=False, **kw):
    """
    return a new query with new constraints expressed in  'django-style'
    
    """
    parser = DjangoParser(mapper, query, or_=or_)

    for key,val in kw.iteritems():
        
        parser.parse( {key:val})
    return parser.compose()


def django2sqlalchemy(mapper, or_=False, **kw):
    """
    return a ClauseList and a join path. 
    """
    parser = DjangoParser(mapper, query=None, or_=or_)

    for key,val in kw.iteritems():
        parser.parse( {key:val})
    return parser.sql(), parser.joins

    
    
if __name__ == '__main__':

    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine, engine
    from sqlalchemy.orm import relation, scoped_session, sessionmaker

    
    Base = declarative_base()
    meta = Base.metadata
    meta.bind = create_engine('sqlite://')
    meta.bind = create_engine('postgres://localhost/c2')
    meta.bind = create_engine('mysql://localhost/c2')
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
#     test(name='ed', addresses__provider__provider__icontains='google', or_=True)
    test(name='ed', addresses__provider__country__country__icontains='ita', or_=True)
    test2(name='ed', addresses__email='@me',
          addresses__provider__country__country__icontains='ita', or_=True)
