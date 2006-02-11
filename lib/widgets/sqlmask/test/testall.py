
import unittest

def suite ():
  modules = ['test_sqlmask']
  tests = unittest.TestSuite ()
  for module in map (__import__, modules):
    tests.addTest (unittest.findTestCases (module, suiteClass = None))
  return tests

if __name__ == '__main__':
  unittest.TextTestRunner (verbosity = 3).run (suite ())
