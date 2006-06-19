#!/usr/bin/env python2.4
# -*- coding: iso-8859-15 -*-

from sqlalchemy import *
import gtk

engine = create_engine('postgres://test@localhost:5433/test')

connection = engine.connect()
result = connection.execute("""SELECT DISTINCT user_name,user_float
         FROM euro_user WHERE user_name = 'Sid'""")

meta = BoundMetaData(engine)
user = Table('euro_user', meta, autoload=True)

for i in result:
    print i.user_name, i.user_float

#import psycopg2 as ps2
import gtk
import psycopg2 as ps2

DB = "host=localhost dbname=test user=test port=5433 password=vicie"
conn = ps2.connect(DB)
cursor = conn.cursor()

query = """SELECT DISTINCT user_float
         FROM euro_user WHERE user_name ~* 'Sid'"""

cursor.execute(query)
conn.commit()
rows = cursor.fetchall()
for row in rows:
    print row[0]

