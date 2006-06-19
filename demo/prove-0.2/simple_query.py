from sqlalchemy import *
import sys, re, datetime

sys.path.append ('../../../')

from sqlalchemy import *
import sqlkit as sk
#import sqlalchemy.mods.threadlocal

#eng = create_engine("sqlite://filename=test-sql.db", echo=False)
#eng = create_engine("sqlite://", echo=False)
#meta = BoundMetaData(eng)
#eng = config.spawnEngine()
global_connect("sqlite://", echo=False)
meta = default_metadata
eng = meta.engine
session = create_session(bind_to=eng)

cities = Table('city_tbl', meta,
              Column('city_id', String(30), primary_key = True, unique=True),
              Column('city_name', String(30), primary_key = True),
              Column('country', String(30), nullable = False),
)
users = Table('user_tbl', meta,
              Column('user_id', Integer, primary_key = True),
              Column('user_name', String(30), nullable = False),
              Column('city_id', String(30), ForeignKey("city_tbl.city_id"), nullable = False),
              Column('user_last_name', String(30), nullable = False))

mails = Table('mail_tbl', meta, 
              Column('mail_address', String(30), nullable = True,
                     primary_key = True),
              Column('user_id', Integer, ForeignKey("user_tbl.user_id")))


# for tbl in (users, cities, mails):
#     try:
#         sd.debug("drop %s" % tbl)
#         tbl.drop()
#     except:
#         pass

#objectstore.commit()

cities.create()                       
users.create()
mails.create()

cities.insert().execute(
    {'city_id' : 1, 'city_name': 'Rome', 'country': 'Italy'},
    {'city_id' : 2, 'city_name': 'Milan', 'country': 'Italy'},
    {'city_id' : 3, 'city_name': 'Paris', 'country': 'Paris'},
    {'city_id' : 4, 'city_name': 'Madrid', 'country': 'Madrid'}
    )
users.insert().execute(
    {'user_id': 1 , 'user_name': 'Sam', 'user_last_name': 'Patts', 'city_id' : '1' },
    {'user_id': 2 , 'user_name': 'Sid', 'user_last_name': 'Watts', 'city_id' : '2' },
    {'user_id': 3 , 'user_name': 'Axe', 'user_last_name': 'Smith', 'city_id' : '3' },
    {'user_id': 4 , 'user_name': 'Ted', 'user_last_name': 'Will' , 'city_id' : '4'  })


mails.insert().execute(
    {'mail_address': 'asam@example.com',  'user_id': 1},
    {'mail_address': 'sid@example.com',  'user_id': 2},
    {'mail_address': 'ated@example.com',  'user_id': 4},
    {'mail_address': 'zted2@example.com', 'user_id': 4})
                       
class User(object): pass
class Mail(object): pass
class City(object): pass



#assign_mapper(User, users)
mail_map = mapper(Mail, mails)
rel = relation(mail_map, lazy=False)
city_map = mapper(City, cities)
rel2 = relation(city_map, lazy=False)

eng.echo = True
m = mapper(User, users, properties = { 'addr': rel, 'cities' : rel2 } )
#user_map = mapper(User, users)

#ret = m.select()
ret = session.query(m).select()
ra = ret[0].addr
rc = ret[0].cities

# print ret[0].addr, len(ret[0].addr)
# print ret[0].cities, len(ret[0].cities)

# users = m.select(order_by="mail_address")
# for u in users:
#     for a in u.addr:
#         print u.user_name,a.mail_address,u.cities.country

M = sk.inspect.InspectMapper(m)
dd = sk.sqldata.SqlData(ret, M, session)
dd.printall()
R = {'user_name' : 'xxx', 'user_last_name' : 'yyy', 'city_id' : 1}
print dd.get_current()
dd.add(R)
session.save(R)

eng.echo = True
session.flush()


