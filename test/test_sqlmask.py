import unittest, sys
from sqlalchemy import *

sys.path.insert('../..')
import sqlkit

import mockup


class SqlMaskTestCase (unittest.TestCase):

  def setUp (self):
    mockup.runBatch ('simpletest.sql')
    self.engine = config.spawnEngine ()
 
  def tearDown (self):
    mockup.runBatch ('dropsimpletest.sql')

  def testSimpleRecordLayout (self):
    t = reflect.mapTable (self.engine, 'test')
    m = reflect.getMapper (t)
    r = reflect.getRecord (m, id = 1)
    layout_before = "l=id e=idval\nl=name e=nameval\nl=date e=dateval\n"
    layout_after = "l=id e=idval\nl=name e=nameval\nl=date e=dateval\nb=annulla b=elimina b=salva"
    s = mask.SqlMask (t, m, r, layout_before)
    self.assertEqual (s.layout, layout_after)

  def testSimpleRecordLayoutGeneration (self):
    t = reflect.mapTable (self.engine, 'test')
    m = reflect.getMapper (t)
    r = reflect.getRecord (m, id = 1)
    s = mask.SqlMask (t, m, r)
    layout = "l=id e=idval\nl=name e=nameval\nl=date e=dateval\nb=annulla b=elimina b=salva"
    self.assertEqual (s.layout, layout)

  def testSimpleLayoutColumnLookup (self):
    t = reflect.mapTable (self.engine, 'test')
    m = reflect.getMapper (t)
    r = reflect.getRecord (m, id = 1)
    m_layout = "l=id e=idval\nl=name e=nameval\nl=date e=dateval\n"
    s = mask.SqlMask (t, m, r, m_layout)
    self.assertEqual (s._findColumnLayout ('name'), 'e=nameval')

  def testSimpleGeneratedLayoutColumnLookup (self):
    t = reflect.mapTable (self.engine, 'test')
    m = reflect.getMapper (t)
    r = reflect.getRecord (m, id = 1)
    s = mask.SqlMask (t, m, r)
    self.assertEqual (s._findColumnLayout ('date'), 'e=dateval')


