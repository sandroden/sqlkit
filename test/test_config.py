import unittest, sys
from sqlalchemy import *

sys.path.insert(0, '../..')
import sqlkit

class ConfigTestCase (unittest.TestCase):

    def testMissingFile(self):
        self.assertRaises(sqlkit.config.MissingConfigFileError,
                          sqlkit.config.searchFile, 'missing.ini')

    def testEngStringURL(self):
        URL = 'postgres://postgres8:xxx@127.0.0.1:5432/test'
        URL_config = sqlkit.config.new_engine(file='tmp/test-url.ini', string=True)
        self.assertEqual(URL, URL_config)

    def testEngString(self):
        URL = 'postgres://postgres8:xxx@127.0.0.1:5432/test'
        URL_config = sqlkit.config.new_engine(file='tmp/test.ini', string=True)
        self.assertEqual(URL, URL_config)

if __name__ == '__main__':
    unittest.main()

  
        
