
import sys

sys.path.append ('../../sqlmask/')

import config
import src.reflect as reflect

from sqlalchemy import *


class Validator (object):

  def validate (self, table = None, record = None):
    self.table = table
    self.record = record
    if self._check (): return True
    else: return False

  def _check (self):
    self.result = {}
    for column in self.table.columns:
      if isinstance (column.type, types.Integer):
        if self._check_int (column, self.record [column.name]):
          self.result [column.name] = True
    print self.result
    return True

  def _check_int (self, column, data):
    state = False
    if isinstance (data, int): state = True
    else: state = False
    if data is None and column.nullable is False: return False
    if state is True:
      return state


if __name__ == '__main__':
  engine = config.spawnEngine ()
  table = reflect.mapTable (engine, 'test2')
  mapper = reflect.getMapper (table)
  record = reflect.getRecord (mapper, id = 1)
  v = Validator ()
  r = {}
  for column in table.columns:
    r [column.name] = getattr (record, column.name)
  v.validate (table, r)
 
