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
Fields
=======
Mask/Tables are collection of data that may belong to the database or not.
Each of the data represented in the GUI that need to partecipate to any
updating/saving process shuld have it's own controller that is a Field.

A Field is an entity that knows how to handle a piece of data, be it on
the database (a field_name) or just in the GUI. It knows:

   - if it belongs to the database (it's attribute mapper is defined) and in
     case how it is defined (sqlalchemy column)
   - if it is nullable
   - which widget must be used to represent it (see below)
   - which locale/format should be used to represent it for numbers/dates/time

It provides functions to

   - set/get value
   - get default value (but cannot always cope with server_side defaults)
   - tell if it changed from the default
   - clean value according to it's logic: i.e. return a value of the correct type
   - validate values (possibly according to other criteria)


Db attributes
-------------

The inspector of the mapper of the sqlwidget sets these values:

   * field_name: the name of the field
   * nullable: True if field is nullable or False
   * editable: True if field is editable or False
   * length: te desired length in chars
   * default: a possible default option
   * type: the python type

   * mapper: defined as None for field that are mapped 
   * table: the SA Table object
   * column: the SA Column object
   * property: the SA Property - if any
   * fkey: the SA ForeignKey or None
   * pkey: True is field is a PRIMARY KEY or False
   
Other attributes
----------------

   * widget:  the widget used to represent it. May be sqlkit.widgets.mask.miniwidget or similar
   * format: the format used to represent the field (numeric or date/time)
   * locale: the locale to use to represent the field (numeric or date/time)
   * DecimalFields also have precision/scale
   * Varchar/TextFields also have blank=True/False (default: False). It determines if an empty string is
     a valid value. Empty strings are differerent from NULL values
     
future
-------
   This should provide a way to set the possible observer

   validation based on the type should live here

   possibly more validation may live here

formatting/locale
-----------------

   see decimal_ to have an intro on formatting numbers

   .. _decimal http://java.sun.com/docs/books/tutorial/i18n/format/decimalFormat.html

FieldChooser
===============

this class implements a way to decide which Field should be associated to each field_name
in a mapper (used in setup_field_validation so that it can be easily overwritten)

Widgets
========

A Field does not create a gtk widget to represent data, that's -rarely- done by
sqlkit.widgets.mask.wiget.Widget. More tipically it is done by the layout procedure and
the Fields/Widget just takes it control and adds completion capabilities.

A notable exception to this rule is represented by any m2m relation, that in the layout is
only present as a gtk.Alignment widget to which a children is added by mask.Widget  

"""
import re
from sqlkit.widgets.mask.miniwidgets import *
from sqlkit.widgets.table.tablewidgets import CellWidget
from datetime import datetime, time, date, timedelta
import gtk
from pprint import pprint 
from sqlalchemy.schema import ColumnDefault
from decimal import Decimal
from sqlkit.misc.babel_support import numbers, dates
from sqlkit import exc, _
import babel

from sqlkit.exc import ValidationError, NotHandledField, NotHandledDefault

class FieldChooser(object):

    """here we wrap the gtk widget in a double layer:

        * field for validation
        * widget for edit

    w:           the widget dictionary retuner by Layout
        
    """

    def __init__(self, master, widgets=None):
        """    
        w:           the widget dictionary retuned by Layout
        master:      the sqlkit widget (SqlMask)
        """
        self.master = master
        self.widgets = widgets or {}

    def get_field(self, field_name, db_spec=None, def_str=None, test=False):
        """return a field

        field_name:  the name of the field in the db
        db_spec:     the dict for this field as worked out by InspectMapper
        def_str:     the definition string in the layout that determined
                     the gtk.Widget (eg.: c=married, e=first_name)
                     as extracted by layoutgen and set in laygen.fields_in_layout dictionary
        """        

        gtk_widget = self.widgets.get(def_str, None)
    
        args = (field_name, db_spec, def_str, self.master, gtk_widget, test)
        if self.master.is_fkey(field_name):
            return ForeignKeyField(*args)

        if self.master.is_loader(field_name):
            return CollectionField(*args)
        
        COL_SPEC = db_spec['col_spec'] or ''

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
        #self.db_spec = db_spec
        self._add_info(db_spec)
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

    def _add_info(self, db_spec):
        self.nullable =  db_spec.get('nullable', True)
        self.editable =  db_spec.get('editable', True)
        self.length   =  db_spec.get('length', None)
        self.default  =  db_spec.get('default', None)
        self.mapper   =  db_spec.get('mapper', None)
        self.pkey     =  db_spec.get('pkey', None)
        self.type     =  db_spec.get('type', None)
        self.property =  db_spec.get('property', None)
        self.column   =  db_spec.get('col', None)
        self.table    =  db_spec.get('table', None)

    def set_value(self, value, initial=True, shown=False):
        value = self.clean_value(value)
        if initial:
            self.initial_value = value
        self.widget.set_value(value)

    def get_value(self, shown=False):
        value = self.widget.get_value(shown=shown)
        return self.clean_value(value)

    def clear_value(self):
        self.set_value(None)

    def set_completion(self, regexp):
        pass

    def has_changed(self, verbose=False):
        """return True if field has changed after last set
        """
#         dbg.write("has_changed - %r: or: %r ==> %r" % (
#             self.field_name, self.initial_value, self.get_value()))

        return not self.get_value() == self.initial_value
    
    def get_default(self):
        """
        return the default value for this object
        """
        value = self.master.get_default(self.field_name)

        if not value:
            try:
                value = self.default
            except KeyError:
                pass
            if isinstance(value, ColumnDefault):
                if not callable(value.arg):
                    return value.arg
                else:
                    ## FIXME: I'm not able to handle this now.
                    raise NotHandledDefault

        return value
        
    def set_default(self):
        try:
            self.set_value(self.get_default())
        except NotHandledDefault:
            pass
        
    def clean_value(self, value):
        """
        return a value of the correct type, if needed parse it with
        locale parsers (numbers, date...)
        """
        return value
   
    def format_value(self, value):
        """
        return a string representaion of the value according to current locale
        value is a "cleaned" value
        """
        return value
    
    def validate(self, value, input_is_fkey=False, clean=False):
        if not clean:
            try:
                value = self.clean_value(value) and True

            except Exception, e:
                msg = "Field %s could not validate value '%s': error was: %s" 
                raise exc.ValidationError(_(msg % (field_name, e.message) ))

        if value is None and not self.nullable:
            raise exc.NotNullableFieldError(self.field_name)

        return value

    def set_max_length(self, editable=None):
        """
        Set max length of the entry used, based on the info from the database
        """
        pass
        
    def __repr__(self):
        return "<%s - %s >" % (self.__class__.__name__, self.field_name)

class VarcharField(Field):
    Widget = VarcharWidget
    
    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.blank = False
        
    def clean_value(self, value):
        if value == '' and not self.blank:
            value = None
        return value

    def set_value(self, value, initial=True, shown=False):
        value = self.clean_value(value)
        if initial:
            self.initial_value = value
        self.widget.set_value(value or '')

    def get_value(self, shown=False):
        value = self.widget.get_value()
        if value == '' and (self.initial_value is None or self.blank is False):
            return None
        return value

    def set_max_length(self):
        if self.length:
            self.widget.set_max_length(self.length)

class IntegerField(Field):
    Widget = IntegerWidget
    
    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.format = "#,###"
        self.locale = babel.default_locale('LC_NUMERIC')
        
    def clean_value(self, value):
        if value in (None, ''):
            return None
        else:
            try:
                if isinstance(value, basestring):
                    value = numbers.parse_number(value, locale=self.locale)
                elif isinstance(value, (int, long)):
                    pass
                else:
                    value = int(value)
            except Exception, e:
                raise exc.ValidationError(e.message)
            return value

    def set_value(self, value, initial=True, shown=False):
        value = self.clean_value(value)
        if initial:
            self.initial_value = value
        self.widget.set_value(self.format_value(value))

    def format_value(self, value):
        if value is None:
            return ''
        return numbers.format_decimal(value, format=self.format, locale=self.locale)
        
class FloatField(IntegerField):
    Widget = FloatWidget

    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.format = "#,###.@"
        self.locale = babel.default_locale('LC_NUMERIC')
        
    def clean_value(self, value):
        if value in (None, ''):
            return None
        else:
            try:
                if isinstance(value, basestring):
                    value = numbers.parse_decimal(value, locale=self.locale)
                elif isinstance(value, float):
                    pass
                else:
                    value = float(value)
            except Exception, e:
                raise exc.ValidationError(e.message)
            return value
        
    def format_value(self, value):
        if value is None:
            return ''
        return numbers.format_decimal(value, format=self.format, locale=self.locale)
        
class DecimalField(IntegerField):
    Widget = DecimalWidget

    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.precision = self.column.type.precision
        self.scale = self.column.type.scale
        self.format = "#,###.%s" % ('0' * self.scale)
        self.format_dec = "#.%s" % ('0' * self.scale)
        self.locale = babel.default_locale('LC_NUMERIC')
        
    def clean_value(self, value):
        if value in (None, ''):
            return None
        else:
            try:
                if isinstance(value, basestring):
                ## why there's no parse_Decimal in babel?
                    value = Decimal(
                        numbers.format_decimal(
                            numbers.parse_decimal(value, locale=self.locale),
                            format=self.format_dec, locale='en')
                        )
                elif isinstance(value, Decimal):
                    pass
                elif isinstance(value, float):
                    value = self.clean_value(str(value))
                else:
                    raise exc.ValidationError(_("value is not Decimal nor string: %s" % value))
            except Exception, e:
                raise exc.ValidationError(e.message)
            return value
        
    def format_value(self, value):
        if value is None:
            return ''
        return numbers.format_decimal(value, format=self.format, locale=self.locale)

class TextField(VarcharField):
    Widget = TextWidget

    def set_max_length(self):
        pass

class DateField(Field):
    Widget = DateWidget
    format = None
        
    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.format = 'short'
        self.locale = babel.default_locale('LC_TIME')
        #if format not in ('short', 'long', 'default', 'medium', 'full'):
        #    pass

    def clean_value(self, value):
        if value in (None, ''):
            return None
        try:
            if isinstance(value, basestring):
                value = dates.parse_date(value)
            elif isinstance(value, date):
                pass
            else:
                raise exc.ValidationError(_("value is not date nor string: %s" % value))
        except Exception, e:
            raise exc.ValidationError(e.message)
        return value
    
    def format_value(self, value):
        return dates.format_date(value, format=self.format, locale=self.locale)
        
class TimeField(DateField):
    Widget = TimeWidget

    def clean_value(self, value):
        if isinstance(value, basestring):
            value = dates.parse_time(value)
        return value
        
    def format_value(self, value):
        return format_time(value, format=self.format, locale=self.locale)
        
class TimeTZField(TimeField):
    Widget = TimeTZWidget

    def clean_value(self, value):
        if isinstance(value, basestring):
            value = dates.parse_time(value)
        return value
        
class IntervalField(Field):
    Widget = IntervalWidget

class DateTimeField(DateField):
    Widget = DateTimeWidget

    def clean_value(self, value):
        if isinstance(value, basestring):
            tmp_date = re.split('\s+', value)
            value = dates.parse_date(tmp_date[0], locale=self.locale)
            if len(tmp_date) >= 1:
                time_list = [int(i) for i in tmp_date[1].split(':')]
            else:
                time_list = []
                
            value = datetime.combine(value, time(*time_list))

                
        return value
        
    def format_value(self, value):
        return dates.format_datetime(value, format=self.format, locale=self.locale)
        
class DateTimeTZField(DateTimeField):
    Widget = DateTimeTZWidget

    def clean_value(self, value):
        if isinstance(value, basestring):
            value = dates.parse_datetime(value)
        return value
        
class BooleanField(Field):
    """
    A simple boolean field that does not allow NULL
    """

    Widget = BooleanWidget

    def clean_value(self, value):
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
    """
    A boolean field that allows to set NULL
    """
    Widget = BooleanNullWidget

    def clean_value(self, value):
        if value not in (True, False, None):
            msg = "Null value not admissable for field %s" % self.field_name
            raise ValidationError(msg) 
        return value
    
class ForeignKeyField(Field):
    """
    A field that uses ComboBoxEntry
    The popup should trigger the filling of the model with
    """
    Widget = ForeignKeyWidget

    def clean_value(self, value, input_is_fkey=False):
        """
        return a cleaned value (i.e.: the foreign key)
        if input_is_fkey=False the text is considered an id, else it's considered a 'search' value
        """
        if input_is_fkey:
            return value
        
        sql = self.widget.completion.compose_select_statement('=', value)
        ret = self.master.metadata.bind.execute(sql).fetchone()
        return ret and ret[0]

    def validate(self, value, input_is_fkey=False, clean=False):
        try:
            value = self.clean_value(value, input_is_fkey=input_is_fkey)
        except Exception, e:
            msg = "Field %s could not validate value '%s': error was: %s" 
            raise exc.ValidationError(_(msg % (self.field_name, value, e.message) ))

        if value is None and not self.nullable:
            raise exc.NotNullableFieldError(self.field_name)

        return value
        
    def get_value(self, shown=False):
        value = self.widget.get_value(shown=shown)
        ## a shown value is not to be transformed
        if not shown and value == '' and self.initial_value is None:
            return None
        return value

    def set_value(self, value, initial=True, shown=False):
        if not shown:
            value = self.clean_value(value, input_is_fkey=True)
        if initial:
            self.initial_value = value
        self.widget.set_value(value, shown=shown)

    def has_changed(self):
        if hasattr(self.widget, 'real_value') and self.widget.real_value == False:
            return True
        else:
            return Field.has_changed(self)
    
class CollectionField(Field):
    """
    A field that uses a SqlTable to show and edit a collection
    in read-wite mode
    Used in OneTomany or ManyToMany db fields

    """
    Widget = CollectionWidget

    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.initial_value = []
        
    def get_default(self):
        ## FIXME: is this always correct?
        return None

    def clean_value(self, value):
        from copy import copy
        
        if value is None:
            value = []
        return copy(value)

    def set_value(self, value, initial=True, shown=False):
        self.initial_value = self.clean_value(value)
        if value is None:
            value = []
        self.widget.set_value(value)





