from sqlalchemy import *
import sys

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

mails = Table('mails', eng,
              Column('mail_address', String(30), nullable = True,
                     primary_key = True),
              Column('user_id', Integer, ForeignKey("users.user_id")))

mails.create()

mails.insert().execute(
    {'mail_address': 'sam@example.com', 'user_id': 1},
    {'mail_address': 'sid@example.com', 'user_id': 2},
    {'mail_address': 'ted@example.com', 'user_id': 4},
    {'mail_address': 'ted2@example.com', 'user_id': 4})
                       
class User(object): pass
class Mail(object): pass
rel = relation(mapper(Mail, mails))
mu = mapper(User, users)
#m = mapper(User, users, properties = { 'addr': rel } )

ret = mu.select()
u = ret[2]

eng.echo = True
# for u in [ret[2]]:
#     for a in u.addr:
#         print u.user_name, a.mail_address
        
u.user_id = 10
objectstore.commit()
