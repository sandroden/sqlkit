
import sys, re, datetime

sys.path.append ('../../../../../../')
import py_path, config, reflect, layout

import gtk, pango
from sqlalchemy import *


class SqlMask (object):

  def __init__ (self, mapper, table, record = None, lay = None, validator = None):
    self.table = table
    self.mapper = mapper
    self.record = record
    self.validator = validator
    if lay is None: self.layout = self.createLayout ()
    else: self.layout = lay
    self.layout += self.addLayoutButtons ()
    self.render = layout.Layout (self.layout)
    self.w = self.render.show ()
    self.postProcess ()

  def createLayout (self):
    entries_layout = []
    for column in self.table.columns:
      if column.foreign_key is not None:
        entries_layout.append (self.addFKLayout (column))
      elif isinstance (column.type, types.Date):
        entries_layout.append (self.addDatetimeLayout (column))
      else:
        entries_layout.append (self.addLabelEntryLayout (column))
    return ''.join (entries_layout)

  def addLabelEntryLayout (self, column):
    return "l=%s e=%s\n" % (column.name, column.name + 'val')

  def addDatetimeLayout (self, column):
    return "l=%s d=%s\n" % (column.name, column.name + 'val')
  
  def addFKLayout (self, column):
    return "l=%s e=%s b=scegli\n" % (column.name, column.name + 'val')

  def addLayoutButtons (self):
    button_layout = ["b=annulla"]
    if self.record is not None: button_layout.append ("b=elimina")
    button_layout.append ("b=salva")
    return ' '.join (button_layout)
  
  def deleteObject (self, widget):
    objectstore.delete (self.record)
    objectstore.commit ()
  
  def saveObject (self, widget):
    if self.record is None:
      record = reflect.Mapper ()
    else:
      record = self.record
    
    for column in self.table.columns:
      c = self._findColumnLayout (column.name)
      if isinstance (column.type, types.Date):
        setattr (record, column.name, self.w [c].get_time ())
      else: setattr (record, column.name, self.w [c].get_text ())
    
    if self.validator is not None:
      r = {}
      for column in self.table.columns:
        r [column.name] = getattr (record, column.name)
      v = self.validator (self.table, r)
      v.validate ()
    
    objectstore.commit ()

  def chooseFK (self, widget, fk):
    # I clearly need to pass arguments to callbacks in GDL
    print fk

  def digitsOnly (self, widget, event):
    key = gtk.gdk.keyval_name (event.keyval)
    if re.match ('[A-Za-z,.\-+()$& ]', key):
      return True

  def postProcess (self):
    for column in self.table.columns:
      column_layout = self._findColumnLayout (column.name)
      self.decorate (column_layout, column)
      if self.record is not None:
        print type (getattr (self.record, column.name))
        if isinstance (getattr (self.record, column.name), datetime.date):
          self.render.prop (column_layout, 'time', getattr (self.record, column.name))
        else:
          self.w [column_layout].set_text (str (getattr (self.record, column.name)))
    self.buttonDispatch ()

  def buttonDispatch (self):
    for key in self.w.keys ():
      rexp = re.compile ('b=(.*)')
      m = rexp.match (key)
      if m:
        if m.group (1) == 'scegli':
          self.render.sig ((key, 'clicked', self.chooseFK, "fk"))
        elif m.group (1) == 'elimina':
          self.render.sig ((key, 'clicked', self.deleteObject))
        elif m.group (1) == 'annulla':
          self.render.connect ((key, 'clicked', lambda l: gtk.main_quit ()))
        elif m.group (1) == 'salva':
          self.render.sig ((key, 'clicked', self.saveObject))

  def decorate (self, column_layout, column):
    if isinstance (column.type, types.String) and column.type.length is not None:
      self.w [column_layout].set_max_length (column.type.length)
    elif isinstance (column.type, types.Integer):
      self.render.connect ((column_layout, 'key_press_event', self.digitsOnly))

  def _findColumnLayout (self, column_name):
    rexp = re.compile ('^.*=%sval$' % column_name)
    for key in self.w.keys ():
      if re.match (rexp, key):
        return key
    return None

