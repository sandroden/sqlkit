from sqlalchemy import *

#eng = create_engine("sqlite://filename=test-sql.db", echo=False)
#eng = create_engine("sqlite://", echo=False)
import sys
sys.path.append ('../../../')
import sqlkit as sk

eng = sk.config.spawnEngine(echo=False)
eng.begin()

city_table = Table('city_tbl', eng,
              Column('city_id', Integer, primary_key = True),
              Column('city_name', String(30)),
              Column('country', String(30), nullable = False)
)
city_table.create()                       
city_table.insert().execute(
    {'city_id': 1, 'city_name': 'Rome',  'country': 'Italy'},
    {'city_id': 2, 'city_name': 'Paris', 'country': 'France'},
    )
users = Table('user_tbl', eng,
              Column('user_id', Integer, primary_key = True),
              Column('user_name', String(30), nullable = False),
              Column('city_id', String(30), ForeignKey("city_tbl.city_id"),
                     nullable = False),
)
users.create()
users.insert().execute(
    {'user_id': 1 , 'user_name': 'Sam', 'city_id' : '1' },
    {'user_id': 2 , 'user_name': 'Sid', 'city_id' : '1' },
    {'user_id': 3 , 'user_name': 'Axe', 'city_id' : '2' },
    {'user_id': 4 , 'user_name': 'Ted', 'city_id' : '2'  })

class User(object): pass
class City(object): pass

c2 = mapper(City, city_table)
rel2 = relation(c2, lazy=False, )

m = mapper(User, users, properties = { 'cities' : rel2 } )

join =  [ city_table.c.city_id == users.c.city_id ]
join += [ city_table.c.city_name.like('%o%')]
join += [ users.c.user_id.op('>')(0)]

#print and_(*join)
eng.echo = True
ret = m.select(and_(*join))
#ret = m.select(and_(*join), limit=10)
#ret = m.select("city_name = 'Rome'", from_obj=[city_table], limit=10)
#ret = m.select("city.city_name = 'Rome' and \
#    city.city_id=users.city_id", from_obj=[city_table], limit=10)


#ret = m.select()
#ret = m.select("user_id > 2", limit=10)
#ret = m.select(city_table.c.city_name == 'Rome' , limit=10)

#ret = m.select_by(city_table.c.city_name.like('Ro%') )
#ret = m.select_by(city_name='Rome' )
#ret = m.select_by("city_name like 'Rome'" )

#ret = m.select("city_name = :city_name" , params={'city_name' : 'Rome'})

for R in ret:
   print R.user_name, R.cities.city_name

eng.rollback()

