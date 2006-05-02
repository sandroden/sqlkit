from sqlalchemy import *

#eng = create_engine("sqlite://filename=test-sql.db", echo=False)
eng = create_engine("sqlite://", echo=False)

cities = Table('city', eng,
              Column('city', String(30), primary_key = True),
              Column('country', String(30), nullable = False)
)
users = Table('users', eng,
              Column('user_id', Integer, primary_key = True),
              Column('user_name', String(30), nullable = False),
              Column('city', String(30), ForeignKey("city.city"), nullable = False),
              Column('user_last_name', String(30), nullable = False))

users.create()
users.insert().execute(
    {'user_id': 1 , 'user_name': 'Sam', 'user_last_name': 'Patts', 'city' : 'Milan' },
    {'user_id': 2 , 'user_name': 'Sid', 'user_last_name': 'Watts', 'city' : 'Rome' },
    {'user_id': 3 , 'user_name': 'Axe', 'user_last_name': 'Smith', 'city' : 'Paris' },
    {'user_id': 4 , 'user_name': 'Ted', 'user_last_name': 'Will' , 'city' : 'Madrid'  })

cities.create()                       
cities.insert().execute(
    {'city': 'Rome', 'country': 'Italy'},
    {'city': 'Milan', 'country': 'Italy'},
    {'city': 'Paris', 'country': 'France'},
    {'city': 'Madrid', 'country': 'Spain'}
    )
class User(object): pass
class City(object): pass

c2 = mapper(City, cities)
rel2 = relation(c2, lazy=False, )

eng.echo = False
m = mapper(User, users, properties = { 'cities' : rel2 } )

ret = m.select()
rc = ret[0].cities

# cit = c2.select()
# for c in cit:
#     for u in c.users:
#         print c.city, c.country, u.user_name


uu = m.select()
for u in uu:
    print u.user_name,u.cities.city
    
