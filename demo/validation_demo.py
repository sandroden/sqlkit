#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, re


sys.path.append ('../../../')
import py_path, config, reflect

from validator import Validator
from errors import *


class EmailValidator (Validator):

  def __init__ (self, table = None, record = None, old_record = None):
    Validator.__init__ (self, table, record)

  def validate (self):
    try:
      self.check ()
    except ValidationError, e:
      print e

  def check (self):
    for column in self.table.columns:
      if column.name == 'mail_address':
        self.check_email (column, self.record [column.name])

  def check_email (self, column, data):
    if re.match (r'^\w[\w\-\.\+]*?@\w[\w\-\.]*?\w\.[a-z]{2,4}$', data) is None:
      raise EmailValidationError (column, data)


class EmailValidationError (ValidationError):

  def __init__ (self, column, data, message = None):
    ValidationError.__init__ (self, column, data, message)

  def __str__ (self):
    message = """
    "%s" non è nel giusto formato per essere inserito in %s.
    """ % (self.data, self.column.name)
    if self.message is not None: return "%s\n%s" % (self.message, message)
    return message


engine = config.spawnEngine ()
table = reflect.mapTable (engine, 'euro_mail')
mapper = reflect.getMapper (table)
record = reflect.getRecord (mapper, mail_user_id = 1)
r = {}
for column in table.columns:
  r [column.name] = getattr (record, column.name)
r ['mail_address'] = 'mail invalida'
v = EmailValidator (table, r)
v.validate ()

