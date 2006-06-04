from sqlalchemy import *
import sys

eng = create_engine("sqlite://", echo=False)

users = Table('users', eng,
       Column('user_name', String(30), nullable = False, primary_key = True),
       Column('user_last_name', String(30), nullable = False))

users.create()

users.insert().execute(
    {'user_name': 'Sam', 'user_last_name': 'Patts'},
    {'user_name': 'Sid', 'user_last_name': 'Watts'},
    {'user_name': 'Axe', 'user_last_name': 'Smith'},
    {'user_name': 'Ted', 'user_last_name': 'Will'})

class User(object): pass

m = mapper(User, users)
#u = m.select()[2]

eng.echo = True

var = {'user_name':'S%'}
ret = m.select("user_name LIKE :user_name", params=var)
for r in ret:
    print r.user_name, r.user_last_name
    
#u.user_id = 10
#u.user_name = 'Sandro'
#objectstore.commit()


