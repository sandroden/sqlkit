# -*- coding: utf-8 -*-

import sys

# sys.path.append ('../../../../')
# import py_path, config, mask, reflect


from sqlalchemy import *

from errors import *


class Validator (object):
  '''
  Base class for validation.
  Type based checking is managed through type_check_dispatcher method.
  To add a new type check for a type with class <typename> add a method
  named _check_<typename> to a derived class.
  '''

  def __init__ (self, table = None, record = None, old_record = None, debug = False):
    self.table = table
    self.record = record
    self.old_record = old_record
    self.debug = debug

  def type_check_dispatcher(self, type_instance, column, column_value):
    type_name = type_instance.__class__.__name__
    # format the name by convention ("_check_<type_name>")
    fname = '_check_' + type_name
    try:
      self.__class__.__dict__[fname](self, column, column_value)
    except KeyError, e:
      #there is not an appropriate function
      return
    

  def validate (self):
    try:
      self._default_check ()
    except ValidationError, e:
      raise e
  def _default_check (self):
    for column in self.table.columns:
      column_value = getattr (self.record, column.name)
      
      self._check_null (column, column_value)
      
      if column.primary_key is True and not reflect.is_serial (column):
        self._check_pkey (column, column_value)
      if column.foreign_key is not None:
        self._check_fkey (column, column_value)

      # simple type checking (mcm) using the type check dispatcher.

      type_check_dispatcher(column.type, column, column_value)
      

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

  def _check_Integer (self, column, data):
    try: data = int (data)
    except ValueError: raise ValidationError (column, data)
    if column.nullable:
      if not isinstance (data, int) and data is not None:
        raise ValidationError (column, data)
    elif not isinstance (data, int):
      raise IntegerValidationError (column, data)

  def _check_String (self, column, data):
    if column.nullable:
      if data is not None and not isinstance (data, str):
        raise ValidationError (column, data)
    elif not isinstance (data, str):
      raise StringValidationError (column, data)
    if column.type.length is not None and column.type.length < len (data):
      raise StringValidationError (column, data,
        message = "La stringa è troppo lunga per essere contenuta da %s" % column.name)

  def _check_Boolean (self, column, data):
    try: data = bool (data)
    except ValueError: raise ValidationError (column, data)
    if column.nullable:
      if data is not None and not isinstance (data, bool):
        raise ValidationError (column, data)
    elif not isinstance (data, bool):
      raise BoolValidationError (column, data)

