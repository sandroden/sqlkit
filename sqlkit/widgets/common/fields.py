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
from datetime import datetime, time, date
import gtk
from pprint import pprint 
from sqlkit.db import defaults

class ValidationError(Exception): pass

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

    def get_field(self, field_name, db_spec, def_str=None):
        """return a field

        field_name:  the name of the field in the db
        db_spec:     the dict for this field as worked out by InspectMapper
        def_str:     the definition string in the layout that determined
                     the gtk.Widget (eg.: c=married, e=first_name)
        """        

        gtk_widget = self.w.get(def_str, None)
    
        args = (field_name, db_spec, def_str, self.master, gtk_widget)
    
        if db_spec['fkey']:
            return ForeignKeyField(*args)

        if self.master.is_loader(field_name):
            return CollectionField(*args)
        
        COL_SPEC = db_spec['col_spec']
        DB_TYPE = db_spec['type']

        if COL_SPEC == 'INTEGER' or DB_TYPE == int:
            return IntegerField(*args)

        if (COL_SPEC and COL_SPEC.startswith('VARCHAR'))  or DB_TYPE == str:
            if isinstance(gtk_widget, gtk.Entry):
                return VarcharField(*args)

        if isinstance(gtk_widget, gtk.TextView) or DB_TYPE == str:
            return TextField(*args)
        
        if COL_SPEC == 'BOOLEAN'  or DB_TYPE == bool:
            if db_spec['nullable']:
                return BooleanNullField(*args)
            else:
                return BooleanField(*args)

        if COL_SPEC == 'DATE'  or DB_TYPE == date:
            return DateField(*args)

        if COL_SPEC == 'TIME' :
            return TimeField(*args)

        if COL_SPEC == 'TIMESTAMP WITHOUT TIME ZONE'  or DB_TYPE == datetime:
            return DateTimeField(*args)

        if COL_SPEC == 'TIMESTAMP WITH TIME ZONE':
            return DateTimeTZField(*args)

        raise NotHandledField("Field %s is not handled in any way")

class Field(object):
    Widget = None
    def __init__(self, field_name, db_spec, def_str, master, gtkwidget):
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
 
        if gtkwidget:
            ## used in SqlMask
            self.widget = self.Widget(gtkwidget, self)
        else:
            ### used in SqlTable
            self.widget = CellWidget(self)

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
        return value
        
    def set_default(self):
        self.set_value(self.get_default())
        
    def clean_initial_value(self, value):
        return value
   
    def validate(self):
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
    Windget = FloatWidget

    def get_value(self, show=False):
        value = self.widget.get_value()
        if value == None:
            return None
        else:
            return float(self.widget.get_value())

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

class DateTimeField(Field):
    Widget = DateTimeWidget

class DateTimeTZField(Field):
    Widget = DateTimeTZWidget

class BooleanField(Field):
    """A simple boolean field that does not allow NULL
    """

    Widget = BooleanWidget

    def clean_initial_value(self, value):
        if value not in (True, False):
            raise ValidationError("Null value not admissable for field %s" % self.field) 

    def clear_value(self):
        ## should I check the default here?
        self.set_value(False)

class BooleanNullField(Field):
    """A boolean field that allows to set NULL
    """
    Widget = BooleanNullWidget

    def clean_initial_value(self, value):
        if value not in (True, False, None):
            raise ValidationError("Null value not admissable for field %s" % self.field) 

    
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

    def __init__(self, field_name, db_spec, def_str, master, gtkwidget):
        Field.__init__(self, field_name, db_spec, def_str, master, gtkwidget)
        self.initial_value = []
        
    def clean_initial_value(self, value):
        from copy import copy
        
        if value is None:
            value = []
        return copy(value)

    def set_value(self, value):
        self.initial_value = self.clean_initial_value(value)
        if value is None:
            value = []
        self.widget.set_value(value)


    
