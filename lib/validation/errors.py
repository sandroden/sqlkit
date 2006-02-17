# -*- coding: utf-8 -*-


class ValidationError (Exception):

  def __init__ (self, column, data, message = None):
    self.column = column
    self.data = data
    self.message = message

  def __str__ (self):
    message = "La colonna %s non può contenere %s" % (self.column.name, self.data)
    if self.message is not None: return "%s\n%s" % (self.message, message)
    return message


class PrimaryKeyValidationError (ValidationError):

  def __init__ (self, column, data, message = None):
    ValidationError.__init__ (self, column, data, message)

  def __str__ (self):
    message = """
    %s è già presente nella colonna %s, è necessario inserire un identificativo univoco.
    """ % (self.data, self.column.name)
    if self.message is not None: return "%s\n%s" % (self.message, message)
    return message


class ForeignKeyValidationError (ValidationError):

  def __init__ (self, column, data, message = None):
    ValidationError.__init__ (self, column, data, message)

  def __str__ (self):
    message = """
    La colonna %s non può contenere %s perchè non corrispondente ad alcun campo di %s.
    """ % (self.column.name, self.data, self.column.foreign_key.column)
    if self.message is not None: return "%s\n%s" % (self.message, message)
    return message


class IntegerValidationError (ValidationError):

  def __init__ (self, column, data, message = None):
    ValidationError.__init__ (self, column, data, message)

  def __str__ (self):
    message = "La colonna %s non può contenere %s perchè non è un intero" % (
        self.column.name, self.data)
    if self.message is not None: return "%s\n%s" % (self.message, message)
    return message


class StringValidationError (ValidationError):
  
  def __init__ (self, column, data, message = None):
    ValidationError.__init__ (self, column, data, message)

  def __str__ (self):
    message = "La colonna %s non può contenere %s perchè non è un intero" % (
        self.column.name, self.data)
    if self.message is not None: return "%s\n%s" % (self.message, message)
    return message

class NullableValidator (ValidationError):

  def __init__ (self, column, data, message = None):
    ValidationError.__init__ (self, column, data, message)

  def __str__ (self):
    message = "La colonna %s non può essere vuota" % (self.column.name)
    if self.message is not None: return "%s\n%s" % (self.message, message)
    return message

