#!/usr/bin/python

from sqlalchemy import *
import sys

sys.path.append ('../../../')

from sqlalchemy import *
import sqlkit as sk

#eng = create_engine("sqlite://filename=test-sql.db", echo=False)
#eng = create_engine("sqlite:///mydb.db", echo=False)
global_connect("sqlite:///mydb.db", echo=False)
eng = schema.default_metadata.engine
session = create_session()

#meta = BoundMetaData(eng)
meta = default_metadata

users_table = Table('user_tbl', meta,
              Column('user_id', Integer, primary_key = True),
              Column('user_name', String(30), nullable = False),
              Column('password', String(30), nullable = False))


#users_table.create()

# users_table.insert().execute(
#     {'user_id': 1 , 'user_name': 'Sam', 'password': 'Patts'},
#     {'user_id': 2 , 'user_name': 'Sid', 'password': 'Watts'},
#     {'user_id': 3 , 'user_name': 'Axe', 'password': 'Smith'},
#     {'user_id': 4 , 'user_name': 'Ted', 'password': 'Will' }   )


class User(object): pass
usermapper = mapper(User, users_table)
sq = session.query(usermapper)

#eng.echo = True
ret = session.query(usermapper).select("user_name LIKE 'S%'")
M = sk.inspect.InspectMapper(usermapper)
dd = sk.sqldata.SqlData(ret, M)
dd.printall()
    
#user.user_name = 'fred jones'
