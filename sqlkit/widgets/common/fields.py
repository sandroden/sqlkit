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
=======
Fields
=======
Mask/Tables are collection of data that may belong to the database or not.
Each of the data represented in the GUI that needs to partecipate to any
updating/saving process should have it's own controller that is a Field.

A Field is an entity that knows how to handle a piece of data, be it on
the database (a field_name) or just in the GUI. It knows:

   - if it belongs to the database (it's attribute mapper is defined) and in
     case how it is defined (sqlalchemy column)
   - if it is nullable
   - which widget must be used to represent it (see below)
   - which locale/format should be used to represent it for numbers/dates/time

It provides functions to

   - set/get value
   - get default value (but will not cope with server_side defaults)
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
   This should provide a way to set the possible observers

   validation based on the type should live here

   possibly more validation may live here

formatting/locale
-----------------

   see decimal_ to have an intro on formatting numbers

.. _decimal: http://java.sun.com/docs/books/tutorial/i18n/format/decimalFormat.html

FieldChooser
===============

This class implements a way to decide which Field should be associated to
each field_name in a mapper (used in setup_field_validation so that it can
be easily overwritten).  It's important to understand that it already
receives a gtkwidget from layoutgenerator; that widget has been set by
introspection on the layout description and of the field in the database.

You can overwrite the decision of the field redefining the gui_field on a
derived sqlwidget::

  class Movie(SqlMask):
      gui_fields = {'date_release' : VarcharField}

  t = Movie(table='movie', dbproxy=db, layout=lay)
  
It's up to the field defined in this way to be able to handle the type of data.
This setting can be used to add field constraints (eg: mail address
validation) or to completely change the widget that represent data.

Widgets
========

A Field does not create a gtk widget to represent data, that's -rarely- done
by sqlkit.widgets.mask.miniwiget.Widget. More tipically it is done by the
layout procedure and the Fields/Widget just takes its control and adds
completion capabilities.

A notable exception to this rule is represented by any m2m relation, that in
the layout is only present as a gtk.Alignment widget to which a children is
added by mask.Widget

Global variables
================

Varchar fields will try to cast an empty value to None unless blank_ok is set
in the field::

    t.gui_field.field_name.blank_ok = True

or globally:

    from sqlkit.widgets.common import fields
    fields.BLANK_OK = True

Default value for BLANK_OK is False.

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
from sqlkit.db import minspect

from sqlkit.exc import ValidationError, NotHandledField, NotHandledDefault
BLANK_OK = False

class FieldChooser(object):

    """here we wrap the gtk widget in a double layer:

        * field for validation
        * widget for edit

    w:           the widget dictionary retuner by Layout
        
    """

    def __init__(self, master, widgets=None):
        """    
        widgets:     the widget dictionary retuned by Layout
        master:      the sqlkit widget (SqlMask)
        """
        self.master = master
        self.widgets = widgets or {}

    def get_field(self, field_name, db_spec=None, def_str=None, test=False):
        """
        return a field

        field_name:  the name of the field in the db
        db_spec:     the dict for this field as worked out by InspectMapper
        def_str:     the definition string in the layout that determined
                     the gtk.Widget (eg.: c=married, e=first_name)
                     as extracted by layoutgen and set in laygen.fields_in_layout dictionary
        """        

        gtk_widget = self.widgets.get(def_str, None)
        args = (field_name, db_spec, self.master, gtk_widget, def_str, test)

        if field_name in self.master.gui_fields:
            return self.master.gui_fields.get(field_name)(*args)


        if self.master.is_fkey(field_name):
            return ForeignKeyField(*args)

        if self.master.is_loader(field_name):
            return CollectionField(*args)
        
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
            if db_spec['col'].type.timezone:
                return TimeField(*args)
            else:
                return TimeField(*args)

        if self.master.is_datetime(field_name):
            if db_spec['col'].type.timezone:
                return DateTimeTZField(*args)
            else:
                return DateTimeField(*args)

        if self.master.is_text(field_name) and not (def_str or '').startswith('e='):
            return TextField(*args)
        
        if self.master.is_string(field_name):
            return VarcharField(*args)

        else:
            return VarcharField(*args)

#         raise NotHandledField("Field '%s' is not handled in any way: COL_SPEC: %s" %
#                               (field_name, db_spec['col_spec']))

class Field(object):
    Widget = None
    default_def_string = 'ae'

    def __init__(self, field_name, db_spec, master, gtkwidget, def_str=None, test=False, widget=None):
        """
        field_name:  the name of the field in the db
        db_spec:     the dict as worked out by InspectMapper
        def_str:     the definition string in the layout that determined
                     the gtk.Widget (eg.: c=married, e=first_name)
        master:      the sqlkit widget: an instance of SqlMask or SqlTable
        widget:      the miniwidget to be used. Defaults to class-define self.Widget
        gtkwidget:   the gtk widget to be used
        """

        self.field_name = field_name
        #self.db_spec = db_spec
        self._add_info(db_spec)
#        self.def_str = def_str
        self.master = master
        self.initial_value = None

        if test:  # in test I don't want conplaints on already prensent widgets
            return

        if def_str and  def_str.startswith('ro='):
            widget = ReadOnlyWidget
            
        Widget = widget or self.Widget
        if gtkwidget:
            ## used in SqlMask
            self.widget = Widget(gtkwidget, self)
        else:
            ### used in SqlTable
            self.widget = CellWidget(self)
        self.master.field_widgets[field_name] = self.widget
        self.set_max_length()

    def set_nullable(self, value):
        self._nullable = value
        self.widget.set_not_null_style()

    def get_nullable(self):
        return self._nullable

    nullable = property(get_nullable, set_nullable)
    
    def _add_info(self, db_spec):
        self._nullable =  db_spec.get('nullable', True)  # don't trigger now widget.set_bg()
        self.editable =  db_spec.get('editable', True)
        self.length   =  db_spec.get('length', None)
        self.default  =  db_spec.get('default', None)
        self.mapper   =  db_spec.get('mapper', None)
        self.pkey     =  db_spec.get('pkey', None)
        self.type     =  db_spec.get('type', None)
        self.property =  db_spec.get('property', None)
        self.column   =  db_spec.get('col', None)
        self.table    =  db_spec.get('table', None)
        if self.pkey:
            self._nullable = False

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
        """
        return True if field has changed after last set
        """
#         dbg.write("has_changed - %r: or: %r ==> %r" % (
#             self.field_name, self.initial_value, self.get_value()))

        try:
            return not self.get_value() == self.initial_value
        except exc.ValidationError:
            # a validation error is a clear sign the values have been changed, but we propabli don't
            # want to cope with them now
            return True
    
    def get_default(self):
        """
        return the default value for this object
        """
        value = self.master.defaults.get(self.field_name)

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
    
    def validate(self, value, clean=False):
        if not clean:
            try:
                value = self.clean_value(value) 

            except Exception, e:
                msg = "Field %s could not validate value '%s': error was: %s" 
                raise exc.ValidationError(_(msg % (field_name, e.message) ))

        if value is None and not self.nullable and not self.default:
            raise exc.NotNullableFieldError(self.field_name, master=self.master)

        self.master.run_hook('on_field_validation', value, self, field_name=self.field_name)

        return True

    def set_max_length(self, editable=None):
        """
        Set max length of the entry used, based on the info from the database
        """
        pass

    def get_human_value(self, value):
        """
        return the value or a translation in human readable for foreign key
        """
        return self.format_value(value)
        
    def __repr__(self):
        return "<%s - %s >" % (self.__class__.__name__, self.field_name)

class VarcharField(Field):
    Widget = VarcharWidget
    
    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        self.blank_ok = BLANK_OK
        
    def clean_value(self, value):
        if value == '' and not self.blank_ok:
            value = None
        return value

    def set_value(self, value, initial=True, shown=False):
        value = self.clean_value(value)
        if initial:
            self.initial_value = value
        self.widget.set_value(value or '')

    def get_value(self, shown=False):
        value = self.widget.get_value()
        if value == '' and (self.initial_value is None or self.blank_ok is False):
            return None
        return value

    def set_max_length(self):
        if self.length:
            self.widget.set_max_length(self.length)

##### Numbers
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
        self.widget.set_value(value)

    def format_value(self, value):
        if value is None:
            return ''
        return numbers.format_decimal(value, format=self.format, locale=self.locale)
        
class FloatField(IntegerField):
    Widget = FloatWidget

    def __init__(self, *args, **kw):
        Field.__init__(self, *args, **kw)
        #self.format = "#.###,000"
        self.format = None
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
        self.format_f = "%%.%sf" % self.scale
        self.locale = babel.default_locale('LC_NUMERIC')
        
    def clean_value(self, value):
        if value in (None, ''):
            return None
        else:
            try:
                if isinstance(value, basestring):
                ## why there's no parse_Decimal in babel?
                    fl = self.format_f % numbers.parse_decimal(value, locale=self.locale)
                    value = Decimal(fl)
                elif isinstance(value, Decimal):
                    pass
                elif isinstance(value, int):
                    value = self.clean_value(str(value))
                elif isinstance(value, float):
                    fl_str = numbers.format_decimal(value, locale=self.locale)
                    value = self.clean_value(fl_str)
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
    default_def_string = 'TXS'

    def set_max_length(self):
        pass

##### Time/Dates
class DateField(Field):
    Widget = DateWidget
    default_def_string = 'd'
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

        if not value:
            return ''

        return dates.format_date(value, format=self.format, locale=self.locale)
        
        
class TimeField(DateField):
    Widget = TimeWidget
    default_def_string = 'ae'

    def clean_value(self, value):

        if isinstance(value, basestring):
            try:
                value = dates.parse_time(value)
            except IndexError, e:
                try:
                    value = dates.parse_time("%s:00" % value)
                except Exception, e:
                    raise exc.ValidationError(e.message)
        return value
        
    def format_value(self, value):
        if not value:
            return ''
        
        if not isinstance(value, time):
            value = self.clean_value(value)

        return dates.format_time(value, format=self.format, locale=self.locale)

class TimeTZField(TimeField):
    Widget = TimeTZWidget

    def __init__(self, *args, **kwargs):
        TimeField.__init__(self, *args, **kwargs)
        self.TZ = None
        
    def clean_value(self, value):
        if isinstance(value, basestring):
            value = dates.parse_time(value)
        return value
        
    def set_value(self, value, initial=True, shown=False):

        TimeField.set_value(self, value, initial=initial)
        
        if initial:
            if value:
                self.TZ = value.tzinfo
                self.microsecond = value.microsecond
            else:
                self.TZ = None
                self.microsecond = 0
        
#     def set_value(self, value):
#         if value:
#             self.TZ = value.tzinfo
#             self.microsecond = value.microsecond
#         else:
#             self.TZ = None
#             self.microsecond = 0

#         if not value:
#             value = ''
#         elif isinstance(value, time):

#             value = value.strftime("%H:%M")
#         self.gtkwidget.set_text(value)

    def get_value(self, shown=False):
        value = self.gtkwidget.get_text() 
        print self, self.field_name, value
        if not self.TZ:
            ## Local will return a tzinfo with the timezone of the system
            ## it will be added to bypass the limitaition od dateedit
            self.TZ = localtimezone.Local
            self.microsecond = 0

        if not value:
            return None
        value = time(*[int(i) for i in re.split('[.:]', value)]) 
        return value.replace(tzinfo=self.TZ, microsecond=self.microsecond)

class IntervalField(Field):
    Widget = IntervalWidget

class DateTimeField(DateField):
    Widget = DateTimeWidget

    def __init__(self, *args, **kwargs):
        DateField.__init__(self, *args, **kwargs)
        self.microsecond = 0
        self.second = 0
        
    def clean_value(self, value, add_second=False, add_microsecond=False):
        """
        parse and return a clean value (ie: a datetime)
        if add_second/add_microsecond, second and microsecond as found in self.(micro)second
        and stored there by set_value are attached to work around widgets that may not be able 
        (or willing) return seconds and microseconds
        """

        if value in (None, ''):
            return None

        if isinstance(value, basestring):
            tmp_date = re.split('\s+', value.strip())
            try:
                date_value = dates.parse_date(tmp_date[0], locale=self.locale)
            except Exception, e:
                raise exc.ValidationError(_('Wrong date format: %s' % tmp_date[0] ))

            try:
                if len(tmp_date) > 1:
                    time_list = [int(i) for i in re.split('[:.]', tmp_date[1]) ]
                else:
                    time_list = []
                time_value = time(*time_list)

            except Exception, e:
                raise exc.ValidationError(_('Wrong time format' ))

            value = datetime.combine(date_value, time_value)

        if isinstance(value, datetime):
            if add_second:
                value = value.replace(second=self.second)
            if add_microsecond:
                value = value.replace(microsecond=self.microsecond)
            
        return value

    def set_value(self, value, initial=True, shown=False):

        Field.set_value(self, value, initial=initial)
        
        if initial:
            if value:
                self.TZ = value.tzinfo
                self.microsecond = value.microsecond
                self.second = value.second
            else:
                self.TZ = None
                self.microsecond = 0
                self.second = 0
        
        
    def format_value(self, value):

        if not value:
            return ''
        
        return dates.format_datetime(value, format=self.format, locale=self.locale)
        
    def get_value(self, shown=False):

        value = self.widget.get_value()

        if value and value.microsecond:
            self.microsecond = value.microsecond
            value = value.replace(microsecond=self.microsecond)

        return value
        
class DateTimeTZField(DateTimeField):
    Widget = DateTimeTZWidget

    def __init__(self, *args, **kwargs):
        DateTimeField.__init__(self, *args, **kwargs)
        self.TZ = None
        self.microsecond = 0
        
    def clean_value(self, value, add_second=False, add_microsecond=False):

        value = DateTimeField.clean_value(self, value, add_second, add_microsecond)

        if not self.TZ:
            ## Local will return a tzinfo with the timezone of the system
            ## it will be added to bypass the limitation of dateedit
            self.TZ = localtimezone.Local
        
        if value:
            if value.tzinfo:
                return value
            else:
                return value.replace(tzinfo=self.TZ)

        return None

    def get_value(self, shown=False):
        """
        Implement a hack around the fact that you normally don't need TZ
        and I don't provide a cell_renderer that gives you the opportunity to change it
        Attach the same timezone as the original data
        """
        value = self.widget.get_value()
        return self.clean_value(value)

##### Boolean
class BooleanField(Field):
    """
    A simple boolean field that does not allow NULL
    """

    Widget = BooleanWidget
    default_def_string = 'c'

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
    
##### Misc
class ForeignKeyField(Field):
    """
    A field that uses ComboBoxEntry
    The popup should trigger the filling of the model with
    """
    Widget = ForeignKeyWidget

    def __init__(self, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
        self._props_for_delete_orphan = minspect.get_props_for_delete_orphan(
            self.master.mapper, self.field_name)
        
    def clean_value(self, value, input_is_fkey=False):
        """
        return a cleaned value (i.e.: the foreign key)
        if input_is_fkey=False the text is considered an id, else it's considered a 'search' value
        """
        if input_is_fkey:
            return value
        
        query = self.widget.completion.compose_select_statement(
            self.widget.completion.query, '=', value)
        ret = query.all()
        #ret = self.master.metadata.bind.execute(sql).fetchone()
        return ret and ret[0]

    def validate(self, value, clean=False):
        """
        for an fkey field a 'clean' value is an fkey, by definition...
        """
        input_is_fkey = clean

        try:
            value = self.clean_value(value, input_is_fkey=clean)
        except Exception, e:
            msg = "Field %s could not validate value '%s': error was: %s" 
            raise exc.ValidationError(_(msg % (self.field_name, value, e.message) ))

        if value is None and not self.nullable:
            raise exc.NotNullableFieldError(self.field_name, master=self.master)

        self.master.run_hook('on_field_validation', value, self, field_name=self.field_name)

        return value
        
    def get_value(self, shown=False):
        value = self.widget.get_value(shown=shown)
        ## a shown value is not to be transformed
        if not shown and value == '' and self.initial_value is None:
            return None
        return value

    def get_human_value(self, value):
        if isinstance(value, (list, tuple)):
            return str([self.widget.completion.lookup_value(v) for v in value])
        return self.widget.completion.lookup_value(value)
    
    def set_value(self, value, initial=True, shown=False):
        if not shown:
            value = self.clean_value(value, input_is_fkey=True)
        if initial:
            self.initial_value = value
        self.widget.set_value(value, shown=shown)
        if value:
            for prop in self._props_for_delete_orphan:
                self.add_related_object(prop, value)

    def has_changed(self):
        ## special case, when is empty
        if self.initial_value is None and self.widget.get_value(shown=True) == '':
            return False
        
        if hasattr(self.widget, 'real_value') and self.widget.real_value == False:
            return True
        else:
            return Field.has_changed(self)

    def add_related_object(self, prop, key):
        """
        Add an object to fullfill the  constraint on delete-orphan 
        """
        if not prop:
            return
        # if the backref that requires this is composed, probably things get more difficoult...
        assert len(prop.mapper.primary_key) ==1, "Sorry, sqlkit doesn't cope with composed primary key in relations with delete-orphan"

        q = self.master.session.query(prop.mapper).autoflush(False)
        obj = q.get(key)
        setattr(self.master.current, prop.key, obj)
        
class CollectionField(Field):
    """
    A field that uses a SqlTable to show and edit a collection
    in read-wite mode
    Used in OneTomany or ManyToMany db fields

    """
    Widget = CollectionWidget

    def __init__(self, field_name, db_spec, master, gtkwidget, def_str, test):
        Field.__init__(self, field_name, db_spec, master, gtkwidget, def_str, test)
        if not test:
            self.widget.table.connect('after_commit', self.set_initial_value)
        self.initial_value = []
        
    def set_initial_value(self, widget, obj, session):
        """
        after_commit the 'new' initial value is the new value...
        """
        self.initial_value = widget.records

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





