"""
fields classes to handle all details:

   set/get value
   add all controls for completion
   possible setup of observer

   validation based on the type should live here

   possibly more validation may live here

   while a
   
"""

from miniwidgets import *
from datetime import datetime, time, date
import gtk
from pprint import pprint 

class FieldChooser(object):

    """here we wrap the gtk widget in a double layer:

        * field for validation
        * widget for edit

    w:           the widget dictionary retuner by Layout
        
    """

    def __init__(self, w, master):
        """    
        w:           the widget dictionary retuned by Layout
        master:      the sqlkit widget (SqlMask)
        """
        self.w = w 
        self.master = master

    def get_field(self, field_name, db_spec, def_str):
        """return a field

        field_name:  the name of the field in the db
        db_spec:     the dict for this field as worked out by InspectMapper
        def_str:     the definition string in the layout that determined
                     the gtk.Widget (eg.: c=married, e=first_name)
        """        

        gtk_widget = self.w[def_str]
    
        args = (field_name, db_spec, def_str, self.master, gtk_widget)
    
        ## FIXME: it doesn't handle OneToMany or ManyToMany
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

        self.widget = self.Widget(gtkwidget, self)

    def set_value(self, value):
        self.widget.set_value(value)

    def get_value(self, shown=None):
        return self.widget.get_value(shown=shown)

    def clear_value(self):
        self.widget.set_value(None)

    def set_completion(self, regexp):
        pass

    def get_changed(self):
        """return if field has changed after last set
        """
        return self.widget.get_changed()
    
    def validate(self):
        pass

    def __repr__(self):
        return "<%s - %s >" % (self.__class__.__name__, self.field_name)

class IntegerField(Field):
    Widget = IntegerWidget
    def get_value(self, shown=False):
        value = self.widget.get_value()
        if value == None:
            return None
        else:
            return int(value)

class FloatField(Field):
    Windget = FloatWidget
    def get_value(self, show=False):
        return float(self.widget.get_value())

class VarcharField(Field):
    Widget = VarcharWidget

class TextField(Field):
    Widget = TextWidget

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

    def clear_value(self):
        ## should I check the default here?
        self.widget.set_value(False)

class BooleanNullField(Field):
    """A boolean field that allows to set NULL
    """
    Widget = BooleanNullWidget

    
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
    
