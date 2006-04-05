import sys
import datetime

sys.path.append ('../../../../../../')
import py_path

from sqlalchemy import *


class TableLayoutGenerator (object):

  def __init__ (self, fields, naked=False):
    """fields: an InspectMapper object"""
    self.layout = self.create (fields)

  def create (self, fields):
    entries = []
    for field_name in fields.keys():
      ftype = getattr(fields, field_name)['type']

      #ftype = fields[field_name]['type']
      
#       if reflect.is_serial (field_name):
#         pass
#       if field_name.foreign_key is not None:
#         entries.append (self.add_foreignkey (field_name))


      if ftype in (datetime.datetime, datetime.date, datetime.time):
        entries.append(self.add_datetime(field_name))

      if ftype == bool:
        entries.append (self.add_boolean (field_name))

      else:
        entries.append (self.add_entry (field_name))
    return ''.join (entries)

  def add_entry (self, field_name):
    return "L=%s e=%s\n" % (field_name, field_name )

  def add_foreignkey (self, field_name):
    return "L=%s e=%s b=scegli\n" % (field_name, field_name)

  def add_datetime (self, field_name):
    return "L=%s d=%s\n" % (field_name, field_name)

  def add_boolean (self, field_name):
    return "L=%s c=%s\n" % (field_name, field_name)



