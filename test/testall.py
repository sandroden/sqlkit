import sys 
sys.path.insert(0, '../..');
import setup

import unittest

def suite ():
    modules = [ 'test_config', 'test_db' ]
    tests = unittest.TestSuite ()
    for module in map (__import__, modules):
        tests.addTest (unittest.findTestCases (module, suiteClass = None))
    return tests

if __name__ == '__main__':
    try:
        setup.drop_tables()
    except:
        pass
    
    setup.prepare_once()
    unittest.TextTestRunner (verbosity = 3).run (suite ())
