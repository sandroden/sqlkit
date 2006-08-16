import sys
sys.path.insert(0, '../..')
import sqlkit as sk
import unittest
from  sqlalchemy import * 

DROP_SQL = """
  DROP TABLE test_mail;
  DROP TABLE test_user;
"""
eng = None

#meta = MetaData()
# users = Table(
#     'test_users', meta, 
#     Column('user_id', Integer, primary_key = True),
#     Column('user_name', String(30), nullable = False),
#     Column('user_last_name', String(30), nullable = False)
#     )

def get_engine():
    global eng
    eng = sk.config.new_engine('test.conf')
    return eng

def prepare_once():
    global eng
    global conn

    #print "PREPARING TABLES..."
    if not eng:
        eng = get_engine()
    conn = eng.connect()
    f = open('test.sql')
    TEST_SQL = f.read()
    f.close()
    conn.execute(TEST_SQL)


def drop_tables():
    global conn
    global eng

    #print "Dropping tables..."
    if not eng:
        eng = get_engine()
        conn = eng.connect()
        
    conn.execute(DROP_SQL)
    

if __name__ == '__main__':
    prepare_once()
    drop_tables()



