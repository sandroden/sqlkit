# Copyright (C) 2008, Sandro Dentella <sandro@e-den.it>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
fields classes to handle all details:

   set/get value
   add all controls for completion
   possible setup of observer

   validation based on the type should live here

   possibly more validation may live here

   while a
   
"""

from sqlkit.widgets.mask.miniwidgets import *
from sqlkit.widgets.table.tablewidgets import CellWidget
from datetime import datetime, time, date, timedelta
import gtk
from pprint import pprint 
from sqlkit.db import defaults
from sqlalchemy.schema import ColumnDefault
from decimal import Decimal

from sqlkit.exc import ValidationError, NotHandledField, NotHandledDefault

class FieldChooser(object):

    """here we wrap the gtk widget in a double layer:

        * field for validation
        * widget for edit

    w:           the widget dictionary retuner by Layout
        
    """

    def __init__(self, master, w=None):
        """    
        w:           the widget dictionary retuned by Layout
        master:      the sqlkit widget (SqlMask)
        """
        self.master = master
        self.w = w or {}

    def get_field(self, field_name, db_spec, def_str=None, test=False):
        """return a field

        field_name:  the name of the field in the db
        db_spec:     the dict for this field as worked out by InspectMapper
        def_str:     the definition string in the layout that determined
                     the gtk.Widget (eg.: c=married, e=first_name)
        """        

        gtk_widget = self.w.get(def_str, None)
    
        args = (field_name, db_spec, def_str, self.master, gtk_widget, test)
        if db_spec['fkey']:
            return ForeignKeyField(*args)

        if self.master.is_loader(field_name):
            return CollectionField(*args)
        
        COL_SPEC = db_spec['col_spec'] or ''
        DB_TYPE = db_spec['type']

        if self.master.is_integer(field_name):
            return IntegerField(*args)

        if self.master.is_float(field_name):
            return FloatField(*args)

        if self.master.is_numeric(field_name):
            return DecimalField(*args)

        if self.master.is_integer(field_name):
            return IntegerField(*args)

        if self.master.is_date(field_name):
            return DateField(*args)

        if self.master.is_boolean(field_name):
            if self.master.is_nullable(field_name):
                return BooleanNullField(*args)
            else:
                return BooleanField(*args)
            
        if self.master.is_interval(field_name):
            return IntervalField(*args)

        if self.master.is_time(field_name):
            if re.search('WITH TIME ZONE', COL_SPEC):
                # FIXME
                return TimeField(*args)
            else:
                return TimeField(*args)

        if self.master.is_datetime(field_name):
            if re.search('WITH TIME ZONE', COL_SPEC):
                return DateTimeTZField(*args)
            else:
                return DateTimeField(*args)

        if self.master.is_text(field_name):
            return TextField(*args)
        
        if self.master.is_string(field_name):
                return VarcharField(*args)


        raise NotHandledField("Field %s is not handled in any way: COL_SPEC: %s" %
                              (field_name, COL_SPEC))

class Field(object):
    Widget = None
    def __init__(self, field_name, db_spec, def_str, master, gtkwidget, test=False):
        """
        field_name:  the name of the field in the db
        db_spec:     the dict as worked out by InspectMapper
        def_str:     the definition string in the layout that determined
                     the gtk.Widget (eg.: c=married, e=first_name)
        master:      the sqlkit widget: an instance of SqlMask or SqlTable
        widget:      the miniwidget to be used
        """

        self.field_name = field_name
        self.db_spec = db_spec
        self.def_str = def_str
        self.master = master
        self.initial_value = None
 
        if test:  # in test I don't want conplaints on already prensent widgets
            return
        
        if gtkwidget:
            ## used in SqlMask
            self.widget = self.Widget(gtkwidget, self)
        else:
            ### used in SqlTable
            self.widget = CellWidget(self)
        self.master.field_widgets[field_name] = self.widget
        self.set_max_length()

    def set_value(self, value, initial=True):
        value = self.clean_initial_value(value)
        if initial:
            self.initial_value = value
        self.widget.set_value(value)

    def get_value(self, shown=None):
        return self.widget.get_value(shown=shown)

    def clear_value(self):
        self.set_value(None)

    def set_completion(self, regexp):
        pass

    def has_changed(self, verbose=False):
        """return True if field has changed after last set
        """
        dbg.write("has_changed - %r: or: %r ==> %r" % (
            self.field_name, self.initial_value, self.get_value()))

        return not self.get_value() == self.initial_value
    
    def get_default(self):
        """
        return the default value for this object
        """

        value = defaults.get_default(self.master.tables, self.field_name)
        if not value:
            try:
                value = self.db_spec['default']
            except KeyError:
                pass
            if isinstance(value, ColumnDefault):
                if not callable(value.arg):
                    return value.arg
                else:
                    ## FIXME: I'm not able to handle thisn now.
                    raise NotHandledDefault

        return value
        
    def set_default(self):
        try:
            self.set_value(self.get_default())
        except NotHandledDefault:
            pass
        
    def clean_initial_value(self, value):
        return value
   
    def validate(self):
        pass

    def set_max_length(self, editable=None):
        """
        Set max length of the entry used, based on the info from the database
        """
        pass
        
    def __repr__(self):
        return "<%s - %s >" % (self.__class__.__name__, self.field_name)

class VarcharField(Field):
    Widget = VarcharWidget
    
    def clean_initial_value(self, value):
        if value == None:
            value = ''
        return value

    def get_value(self, shown=False):
        value = self.widget.get_value()
        if value == '' and self.initial_value is None:
            return None
        return value

    def set_max_length(self):
        if self.db_spec['length']:
            self.widget.set_max_length(self.db_spec['length'])

class IntegerField(Field):
    Widget = IntegerWidget
    def get_value(self, shown=False):
        value = self.widget.get_value()
        if value in (None, ''):
            return None
        else:
            return int(value)

    def clean_initial_value(self, value):
        if value == '':
            return None
        else:
            return value

class FloatField(IntegerField):
    Widget = FloatWidget

    def get_value(self, shown=False):
        value = self.widget.get_value()
        if value == None:
            return None
        else:
            return float(self.widget.get_value())

class DecimalField(IntegerField):
    Widget = DecimalWidget

    def get_value(self, shown=False):
        value = self.widget.get_value()
        if value == None:
            return None
        else:
            return Decimal(self.widget.get_value())

class TextField(Field):
    Widget = TextWidget

    def clean_initial_value(self, value):
        if value is None:
            value = ''
        return value    
        
class DateField(Field):
    Widget = DateWidget

class TimeField(Field):
    Widget = TimeWidget

class TimeTZField(Field):
    Widget = TimeTZWidget

class IntervalField(Field):
    Widget = IntervalWidget

class DateTimeField(Field):
    Widget = DateTimeWidget

class DateTimeTZField(Field):
    Widget = DateTimeTZWidget

class BooleanField(Field):
    """A simple boolean field that does not allow NULL
    """

    Widget = BooleanWidget

    def clean_initial_value(self, value):
        if value is None:
            value = False
        if value not in (True, False):
            msg = "Null value not admissable for field %s" % self.field_name
            raise ValidationError(msg) 
        return value
    
    def clear_value(self):
        ## should I check the default here?
        self.set_value(False)

class BooleanNullField(Field):
    """A boolean field that allows to set NULL
    """
    Widget = BooleanNullWidget

    def clean_initial_value(self, value):
        if value not in (True, False, None):
            msg = "Null value not admissable for field %s" % self.field_name
            raise ValidationError(msg) 
        return value
    
class ForeignKeyField(Field):
    """A field that uses ComboBoxEntry
    The popup should trigger the filling of the model with
    """
    Widget = ForeignKeyWidget

class CollectionField(Field):
    """A field that uses a SqlTable to show and edit a collection
    in read-wite mode
    Used in OneTomany or ManyToMany db fields

    """
    Widget = CollectionWidget

    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.initial_value = []
        
    def clean_initial_value(self, value):
        from copy import copy
        
        if value is None:
            value = []
        return copy(value)

    def set_value(self, value, initial=True):
        self.initial_value = self.clean_initial_value(value)
        if value is None:
            value = []
        self.widget.set_value(value)


    




