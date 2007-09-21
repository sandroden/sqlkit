import unittest, sys
from sqlalchemy import *
import decimal
import datetime

sys.path.insert(0, '../..')
import sqlkit as sk
import setup


class DbConnTestCase(unittest.TestCase):

    def testText(self):
        text = setup.eng.text("SELECT 1")
        text.execute()

    def testConn(self):
        setup.conn.execute("SELECT 1")

    def testFloat(self):
        ret = setup.conn.execute("SELECT 1.23::float AS foo")
        result = ret.fetchone()[0]
        self.assertEqual(result, 1.23)

    def testFloatGTK(self):
        import gtk
        ret = setup.conn.execute("SELECT 1.23::float AS foo")
        result = ret.fetchone()[0]
        self.assertEqual(result, 1.23)

class DbInspect(unittest.TestCase):

    def setUp(self):
        self.user = Table('test_user', setup.eng, autoload=True)
        class User(object): pass
        self.mapper = mapper(User, self.user)
        self.fields = sk.minspect.InspectMapper(self.mapper)

        self.mail = Table('test_mail', setup.eng, autoload=True)
        class Mail(object): pass
        self.mapper2 = mapper(Mail, self.mail)
        self.fields2 = sk.minspect.InspectMapper(self.mapper2)

    # ['pkey', 'name', 'nullable', 'edit', 'is_serial', 'col', 'col_spec',
    # 'length', 'table_name', 'fkey', 'table', 'property', 'type', 'pg_type',
    # 'mapper']

    def testInspect__col_spec(self):
        #print self.fields['user_id'].keys()
        flds = {
            'user_id' :         'INTEGER',
            'user_name' :       'VARCHAR(30)',
            'user_last_name' :  'VARCHAR(30)',
            'user_birth_date' : 'TIMESTAMP',
            'user_address' :    'VARCHAR(20)',
            'user_city' :       'VARCHAR(20)',
            'user_pv' :         'CHAR(2)',
            'user_age' :        'INTEGER',
            'user_sex' :        'CHAR(1)',
            'user_active' :     'BOOLEAN',
            'user_timestamp' :  'TIMESTAMP',
            'user_fee'       :  'NUMERIC(8, 2)',
            'user_float'     :  'FLOAT(53)',
            
            }
        for f in self.fields.keys():
            #print f, self.fields[f]['col_spec']
            self.assertEqual(flds[f], self.fields[f]['col_spec'])

    def test__is_serial_true(self):
        self.assertEqual(self.fields['user_id']['is_serial'], True)
        
    def test__is_serial_false(self):
        self.assertEqual(self.fields['user_name']['is_serial'], False)

    def test_pk_true(self):
        self.assertEqual(self.fields['user_id']['pkey'], True)
        
    def test_pk_false(self):
        self.assertEqual(self.fields['user_name']['pkey'], False)
        
    def testInspect__lenght(self):
        flds = {
            'user_id' :           None,
            'user_name' :         30  ,
            'user_last_name' :    30  ,
            'user_birth_date' :   None,
            'user_address' :      20  ,
            'user_city' :         20  ,
            'user_pv' :           2   ,
            'user_age' :          None,
            'user_sex' :          1   ,
            'user_active' :       None,
            'user_timestamp' :    None,
            'user_fee'       :    2   ,
            'user_float'     :    None,
            }
        for f in self.fields.keys():
            self.assertEqual(flds[f], self.fields[f]['length'])

    def testInspect__type(self):
        flds = {
            'user_id' :           int                ,
            'user_name' :         str                ,
            'user_last_name' :    str                ,
            'user_birth_date' :   datetime.datetime  ,
            'user_address' :      str                ,
            'user_city' :         str                ,
            'user_pv' :           str                ,
            'user_age' :          int                ,
            'user_sex' :          str                ,
            'user_active' :       bool               ,
            'user_timestamp' :    datetime.datetime  ,
            'user_fee'       :    decimal.Decimal    ,
            'user_float'     :    float              ,
            }
        for f in self.fields.keys():
            self.assertEqual(flds[f], self.fields[f]['type'])

    def testInspect__fk(self):
        self.assertEqual(self.fields2['mail_user_id']['fkey'],
                         ('test_user', 'user_id'))

    def testInspect__pk(self):
        self.assertEqual(self.fields.get_pkeys('test_user'), ['user_id'])
        self.assertEqual(self.fields2.get_pkeys('test_mail'), ['mail_address'])



if __name__ == '__main__':
    try:
        setup.drop_tables()
    except:
        pass
    
    setup.prepare_once()
    #unittest.TextTestRunner (verbosity = 3).run ()
    unittest.main()
    













