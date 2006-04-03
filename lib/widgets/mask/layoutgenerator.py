import sys

sys.path.append ('../../../../../../')
import py_path, reflect

from sqlalchemy import *


class TableLayoutGenerator (object):

  def __init__ (self, table, naked=False):
    self.table = table
    self.layout = self.create ()

  def create (self):
    entries = []
    for column in self.table.columns:
#       if reflect.is_serial (column):
#         pass
      if column.foreign_key is not None:
        entries.append (self.add_foreignkey (column))
      elif isinstance (column.type, types.Date) or isinstance (
        column.type, types.DateTime):
        entries.append (self.add_datetime (column))
      elif isinstance (column.type, types.Boolean):
        print type(column.type)
        entries.append (self.add_boolean (column))
      else:
        entries.append (self.add_entry (column))
    return ''.join (entries)

  def add_entry (self, column):
    return "L=%s e=%s\n" % (column.name, column.name )

  def add_foreignkey (self, column):
    return "L=%s e=%s b=scegli\n" % (column.name, column.name)

  def add_datetime (self, column):
    return "L=%s d=%s\n" % (column.name, column.name)

  def add_boolean (self, column):
    return "L=%s c=%s\n" % (column.name, column.name)



