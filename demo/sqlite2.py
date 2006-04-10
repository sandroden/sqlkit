from sqlalchemy import *
import sys, re, datetime

sys.path.append ('../../../')
import py_path, config, reflect, mask
import sd
sd.dbg = 1

from sqlalchemy import *
from layout import *
from validator import Validator

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

mails = Table('mails', eng,
              Column('mail_address', String(30), nullable = True,
                     primary_key = True),
              Column('user_id', Integer, ForeignKey("users.user_id")))

mails.create()

mails.insert().execute(
    {'mail_address': 'sam@example.com',  'user_id': 1},
    {'mail_address': 'sid@example.com',  'user_id': 2},
    {'mail_address': 'ted@example.com',  'user_id': 4},
    {'mail_address': 'ted2@example.com', 'user_id': 4})
                       
cities.create()                       
cities.insert().execute(
    {'city': 'Rome', 'country': 'Italy'},
    {'city': 'Milan', 'country': 'Italy'},
    {'city': 'Paris', 'country': 'Paris'},
    {'city': 'Madrid', 'country': 'Madrid'}
    )
class User(object): pass
class Mail(object): pass
class City(object): pass

m2 = mapper(Mail, mails)
rel = relation(m2, lazy=False)
c2 = mapper(City, cities)
rel2 = relation(c2, lazy=False)

eng.echo = True
m = mapper(User, users, properties = { 'addr': rel, 'cities' : rel2 } )

ret = m.select()
ra = ret[0].addr
rc = ret[0].cities

# print ret[0].addr, len(ret[0].addr)
# print ret[0].cities, len(ret[0].cities)

users = m.select()
for u in users:
    print u
    for a in u.addr:
        print a
    for c in u.cities:
        print c
                        

