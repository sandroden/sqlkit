# -*- coding: utf-8 -*-

import sys

sys.path.append ('../../../../')
import py_path, config, mask, reflect

from sqlalchemy import *

from errors import *


class Validator (object):

  def __init__ (self, table = None, record = None, old_record = None, debug = False):
    self.table = table
    self.record = record
    self.old_record = old_record
    self.debug = debug

  def validate (self):
    try:
      self._check ()
    except ValidationError, e:
      return e

  def _check (self):
    for column in self.table.columns:
      self._check_null (column, self.record [column.name])
      if column.primary_key is True:
        self._check_pkey (column, self.record [column.name])
      if column.foreign_key is not None:
        self._check_fkey (column, self.record [column.name])
        
      if isinstance (column.type, types.Integer):
        self._check_int (column, self.record [column.name])
      elif isinstance (column.type, types.String):
        self._check_str (column, self.record [column.name])
      elif isinstance (column.type, types.Boolean):
        self._check_bool (column, self.record [column.name])

  def _check_null (self, column, data):
    if data is None and not column.nullable:
      raise NullableValidationError

  def _check_pkey (self, column, data):
    fetch_pkey = select ([column], column == data).execute ()
    if fetch_pkey.fetchone () is not None:
      raise PrimaryKeyValidationError (column, data)

  def _check_fkey (self, column, data):
    fetch_fkey = select ([column.foreign_key.column], column.foreign_key.column == data).execute ()
    if fetch_fkey.fetchone () is None:
      raise ForeignKeyValidationError (column, data)

  def _check_int (self, column, data):
    if column.nullable:
      if data is not None and not isinstance (data, int):
        raise ValidationError (column.name, data)
    elif not isinstance (data, int):
      raise IntegerValidationError (column, data)

  def _check_str (self, column, data):
    if column.nullable:
      if data is not None and not isinstance (data, str):
        raise ValidationError (column, data)
    elif not isinstance (data, str):
      raise StringValidationError (column, data)
    if column.type.length is not None and column.type.length < len (data):
      raise StringValidationError (column, data,
        message = "La stringa è troppo lunga per essere contenuta da %s" % column.name)

  def _check_bool (self, column, data):
    if column.nullable:
      if data is not None and not isinstance (data, bool):
        raise ValidationError (column, data)
    elif not isinstance (data, bool):
      raise BoolValidationError (column, data)


if __name__ == '__main__':
  engine = config.spawnEngine ()
  table = reflect.mapTable (engine, 'euro_mail')
  mapper = reflect.getMapper (table)
  record = reflect.getRecord (mapper, mail_user_id = 1)
  r = {}
  for column in table.columns:
    r [column.name] = getattr (record, column.name)
  v = Validator (table, r)
  v.validate ()
 
