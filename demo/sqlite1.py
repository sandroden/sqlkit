from sqlalchemy import *

eng = create_engine("sqlite://", echo=False)

users = Table('users', eng,
              Column('user_id', Integer, primary_key = True),
              Column('user_name', String(30), nullable = False),
              Column('user_last_name', String(30), nullable = False))

users.create()

users.insert().execute(
    {'user_name': 'Sam', 'user_last_name': 'Patts'},
    {'user_name': 'Sid', 'user_last_name': 'Watts'},
    {'user_name': 'Axe', 'user_last_name': 'Smith'},
    {'user_name': 'Ted', 'user_last_name': 'Will'})

class User(object): pass

m = mapper(User, users)
u = m.select()[2]

eng.echo = True

r = text("SELECT * FROM users WHERE user_name LIKE :user_name ", engine=eng)
#r.execute()
ret = r.execute(**{'user_name' : 'S%'})
for R in ret: 
    print R.user_id, R.user_name
#u.user_id = 10
#u.user_name = 'Sandro'
#objectstore.commit()
