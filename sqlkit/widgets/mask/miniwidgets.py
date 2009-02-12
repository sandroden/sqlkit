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
Gtk Widgets
===========

widgets to be used by fields to display values and edit 
at the time of writing, intial value is stored here but should be moved to fields
widgets only interpret gtk, while fields teat with real values and do validation


"""


from sqlkit.widgets.common import localtimezone
import gtk
from sqlkit import debug as  dbg
from datetime import timedelta, time
from sqlkit.widgets.common.completion import SimpleCompletion, FkeyCompletion
import re
from decimal import Decimal
import gobject

NOT_NULL_COLOR = gtk.gdk.color_parse('LightGoldenrod')


class Widget(object):
    def __init__(self, gtkwidget, field):
        self.gtkwidget = gtkwidget
        self.field = field
        self.master = field.master
        self.field_name = field.field_name
        self.set_not_null_style()
        gtkwidget.set_property('sensitive', self.field.db_spec['editable']) 

    def set_not_null_style(self):
        if self.field.db_spec['editable']:
            if not self.field.db_spec['nullable'] or self.field.db_spec['pkey']:
                self.set_bg()

    def set_bg(self, state=gtk.STATE_NORMAL,  color=NOT_NULL_COLOR):
        self.gtkwidget.modify_base(state, NOT_NULL_COLOR)
        
    def set_value(self, value, shown=False):
        """if shown is True, the displayed value is returned also in any
        case. The difference is only for ForeignKey
        The displayed value may be used for completion purpouses
        """
        pass

    def get_value(self):
        pass

    def get_entry(self):
        """
        return the entry on which you want to apply completion for this object
        """
        return self.gtkwidget

    def __repr__(self):
        return "< %s - %s >" % (self.__class__.__name__, self.field_name)

class VarcharWidget(Widget):
    #  to prevent to change NULL to '' and viceversa
    #  we store the value when setting it 
    #  and compare it when getting

    def __init__(self, *args):

        Widget.__init__(self, *args)
        self.add_completion()

    def add_completion(self):
        """add completion bindings and liststore
        """
        self.completion = SimpleCompletion(self.master, self, self.field_name)
        self.completion.add_completion(self.gtkwidget)
        self.master.completions[self.field_name] = self.completion
        self.completion.add_callbacks(self.gtkwidget)

    def set_value(self, value):
        # Entry
        self.gtkwidget.set_text( str(value) )
        
    def get_value(self, shown=False):
        value = self.gtkwidget.get_text( )
        ## don't change from None to '' 
        return value

    def set_max_length(self, length):
        self.gtkwidget.set_max_length(length)
        
class IntegerWidget(VarcharWidget):

    def __init__(self, *args):
        Widget.__init__(self, *args)
        self.gtkwidget.set_alignment(1)
        self.gtkwidget.connect('key-press-event', self.master.digits_check_input_cb  )
                
    def set_value(self, value):
        # Entry
        if value is None:
            txt_value = ''
        else:
            txt_value = str(value)
            
        self.gtkwidget.set_text(txt_value)
        
    def get_value(self, shown=False):
        text = self.gtkwidget.get_text( )
        return self.field.clean_value(text)

class FloatWidget(IntegerWidget):
    pass

class DecimalWidget(IntegerWidget):
    pass

class DateWidget(Widget):

    def __init__(self, *args):
        Widget.__init__(self, *args)
        self.gtkwidget.set_property('show-time', False)

    def set_value(self, value):
        self.gtkwidget.set_property('time', value)

    def get_value(self, shown=False):
        return self.gtkwidget.get_property('time')

class TimeWidget(Widget):

    def set_value(self, value):
        if not value:
            value = ''
        elif isinstance(value, time):
            value = value.strftime("%H:%M")
        self.gtkwidget.set_text(value)

    def get_value(self, shown=False):
        value = self.gtkwidget.get_text() 
        if not value:
            return None
        return time(*[int(i) for i in re.split('[.:]', value)])


class TimeTZWidget(Widget):

    def set_value(self, value):
        if value:
            self.TZ = value.tzinfo
            self.microsecond = value.microsecond
        else:
            self.TZ = None
            self.microsecond = 0

        if not value:
            value = ''
        elif isinstance(value, time):

            value = value.strftime("%H:%M")
        self.gtkwidget.set_text(value)

    def get_value(self, shown=False):
        value = self.gtkwidget.get_text() 
        if not self.TZ:
            ## Local will return a tzinfo with the timezone of the system
            ## it will be added to bypass the limitaition od dateedit
            self.TZ = localtimezone.Local
            self.microsecond = 0

        if not value:
            return None
        value = time(*[int(i) for i in re.split('[.:]', value)]) 
        return value.replace(tzinfo=self.TZ, microsecond=self.microsecond)


class IntervalWidget(Widget):

    def set_value(self, value):
        if value and not isinstance(value, timedelta):
            msg = "value for %s must be a timedelta (now: %s)" % (self.field_name, value)
            raise AttributeError(msg)
        self.gtkwidget.set_property('interval', value)

    def get_value(self, shown=False):
        ## if all values are 0 and initial value is None, return None
        
        value = self.gtkwidget.get_property('interval') 
        if value == timedelta(0) and self.field.initial_value == None:
            return None
        return value

class DateTimeWidget(DateWidget):

    def __init__(self, *args):
        Widget.__init__(self, *args)
        self.gtkwidget.set_property('show-time', True)
        self.initial_delta = timedelta(0)
        
    def set_value(self, value):
        ## FIXME: datetime has only time?
        self.gtkwidget.set_property('time', value)

        if value:
            self.microsecond = value.microsecond
        else:
            self.microsecond = 0

    def get_value(self, shown=False):
        value = self.gtkwidget.get_property('time')
        if value:
            return value.replace(microsecond=self.microsecond)
        return value 

class DateTimeTZWidget(DateTimeWidget):

    def set_value(self, value):
        ## FIXME: datetime has only time?
        self.gtkwidget.set_property('time', value)
        ## the gtkwidget does not show the TZ info and does not give it back
        ## so we store the original value
        if value:
            self.TZ = value.tzinfo
            self.microsecond = value.microsecond
        else:
            self.TZ = None
            self.microsecond = 0

    def get_value(self, shown=False):
        value = self.gtkwidget.get_property('time')
        if not self.TZ:
            ## Local will return a tzinfo with the timezone of the system
            ## it will be added to bypass the limitaition od dateedit
            self.TZ = localtimezone.Local
            self.microsecond = 0

        if value:
            return value.replace(tzinfo=self.TZ, microsecond=self.microsecond)
        return None


class TextWidget(Widget):

    def __init__(self, *args):
        Widget.__init__(self, *args)
        self.gtkwidget.set_property('wrap-mode', gtk.WRAP_WORD)

    def set_value(self, value):
        buff = self.gtkwidget.get_buffer()
        buff.set_text( value)

    def get_value(self, shown=False):
        buff = self.gtkwidget.get_buffer()
        ts = buff.get_iter_at_offset(0)
        te = buff.get_iter_at_offset(-1)
        text = buff.get_text(ts, te)
        return text
        

class BooleanWidget(Widget):
    """Null value is not admittable"""

    def set_value(self, value):
        self.gtkwidget.set_active(bool(value))

    def get_value(self, shown=False):
        return self.gtkwidget.get_active( )
        
class BooleanNullWidget(Widget):
    """This gtkwidget is placed in inconsinstent state to represent NULL
    """

    def set_value(self, value):
        if value == None:
            self.gtkwidget.set_inconsistent(True)
        else:
            self.gtkwidget.set_active(value)
            self.gtkwidget.set_inconsistent(False)

    def get_value(self, shown=False):
        if self.gtkwidget.get_inconsistent():
            return None
        else:
            return self.gtkwidget.get_active( )
            
class ForeignKeyComboboxWidget(Widget):
    """a ComboBoxEntry with 2 columns

    In any case for the moment we need to click on a choice from the completion
    (we cannot just write a correct value), since completion also retrieves the id
    """

    def __init__(self, *args):

        Widget.__init__(self, *args)
        ## see completion.append_to_model() to understand the meaning of these 4 columns
        # add to a model that has 4 cols:
        #       0: the value to be used as foreign key
        #       1: the value to be shown in the entry 
        #       2: data to be shown in the dropdown
        #       3: a dictionary of all fields in the returned row
        #          this can be used to set additional fields
                    

        self.model = gtk.ListStore(object, str, str, object)

#        self.gtkwidget.connect('changed', self.clean_real_value)
        self.gtkwidget.set_model(self.model)
        self.gtkwidget.set_text_column(2)

        self.gtkwidget.connect(
            'button-press-event', self.completion.pop_menu, self.field_name, 3)
        self.gtkwidget.connect(
            'key-press-event', self.completion.keypress_event_cb, self.field_name)
        self.entry = self.gtkwidget.child
        completion = self.completion.prepare_completion(self.field_name, mode='regexp',
                                                               match_col=2)
        completion.set_model(self.model)
        self.entry.set_completion(completion)
        self.gtkwidget.connect('notify::popup-shown', self.on_popup)        

    def on_popup(self, widget, params):
        """the popup should be empty. We force the completion instead
        """
        self.completion.show_possible_completion(self.gtkwidget, mode='regexp')
            
        return True

    def clean_real_value(self, *args):
        ## the EntryText has been changed. The value may no longe be  valid
        self.real_value = False

    def set_value(self, value):
        """We have a 'real_value' that is normally an id or a key and a 'display_value'
        that is the value we want to show
        """
        display_value = self.completion.lookup_value(self.field_name, value)
        if value == None:
            if self.field.db_spec['type'] == str:
                value = ''

        self.model.clear()
        self.model.append([value, display_value, display_value,''])
        self.gtkwidget.set_active(0)   # which column 
#        self.real_value = True  ?????

        #self.gtkwidget.set_text( str(value) )
        
    def get_value(self, shown=False):
        #dbg.write()

        if shown == True:
            ## this is for completion. The value needed is the value in the entry not in the model
            return self.entry.get_text()

        idx = self.gtkwidget.get_active()
        value, display_value, descr, obj_dict = self.model[idx]

        return  value

class ForeignKeyWidget(Widget):
    """a ComboBoxEntry with 2 columns

    In any case for the moment we need to click on a choice from the completion
    (we cannot just write a correct value), since completion also retrieves the id
    """

    def __init__(self, *args):

        Widget.__init__(self, *args)

        self.entry  = self.gtkwidget.entry
        self.button = self.gtkwidget.button
        self.add_completion()
        self.real_value = True
        self.master.completions[self.field_name] = self.completion
        self.set_not_null_style()

    def add_completion(self):
        """add completion bindings and liststore
        """
        self.completion = FkeyCompletion(self.master, self, self.field_name)
        self.completion.add_completion(self.entry)
        self.master.completions[self.field_name] = self.completion

        ## button connect
        self.button.connect('button-press-event', self.completion.pop_menu,  self.field_name, 3)
        self.button.connect('clicked', self.on_button_clicked)

        ## entry connect
        self.completion.add_callbacks(self.entry)

    def on_button_clicked(self, widget):

        self.completion.show_possible_completion(self.entry, mode='regexp')
        return True

    def on_key_press(self, widget, event, when='press'):

        return self.completion.keypress_event_cb(self.entry, event, self.field_name, when)

    def on_entry_changed(self, editable):

        self.real_value = False

    def clean_real_value(self, *args):
        ## the EntryText has been changed. The value may no longe be  valid
        self.real_value = False

    def is_valid(self):
        return self.real_value

    def set_value(self, value, shown=False):
        """
        We have a real 'value' that is normally an id or a key and a 'display_value'
        that is the value we want to show
        shown: the passed value is a value to be shown.
               a shown value is not cleaned (e.g.: for completion)
        """
        if shown:
            display_value = value
        else:
            self.value = value
            display_value = self.completion.lookup_value(self.field_name, value)
            self.real_value = True  # we can trust this value, has been set by procedures
            
        self.entry.set_text(display_value)
        
    
    def get_value(self, shown=False):
        if shown:
            return self.entry.get_text() 
        if self.real_value:
            return self.value
        else:
            raise NotImplementedError

class CollectionWidget(Widget):
    """
    a SqlTable widget that represents a collection of records
    """
    def __init__(self, *args):
        
        Widget.__init__(self, *args)
        table = self.field.db_spec['table']

        from sqlkit.widgets import SqlTable
        loader_spec = self.master.laygen.loaders[self.field_name]

        direction = self.field.db_spec['property'].direction.name
        if direction  == 'MANYTOMANY':
            direction = "m2m"
        elif direction == 'ONETOMANY':
            direction = "o2m"

        self.table = SqlTable(
            table=table.name,
            geom = (-1, -1),
            rows = loader_spec.get('rows', 5),
            mapper = self.field.db_spec['mapper'],
            session=self.master.session,
            metadata=self.master.metadata,
            dbproxy=self.master.dbproxy,
            naked=True,
            col_width = filter_related(self.master.col_width, self.field_name),
            field_list = loader_spec.get('field_list', None),
            addto=self.gtkwidget,
            icons='b=gtk-new b=gtk-delete b=gtk-save b=gtk-zoom-fit',
            ignore_fields = self.field.db_spec['remote_attr'],
            dev = self.master.dev,
            relationship_leader = self.master,
            relationship_mode = direction,
            relationship_path = self.master.relationship_path + [self.field_name],
            label_map = self.prepare_label_map()
            )
        
        # We generally want a table to expand if possible        
        parent = self.gtkwidget.get_parent()
        if parent:
            prop_names = [prop.name for prop in parent.list_child_properties()]
            if 'y-options' in prop_names:
                parent.child_set_property(self.gtkwidget, 'y-options', gtk.EXPAND | gtk.FILL)
            if isinstance(parent, gtk.VBox):
                parent.child_set_property(self.gtkwidget, 'expand', True)
        

#         if self.field_name in self.master.laygen.loaders:
#             self.table.set_field_list(self.master.laygen.loaders[self.field_name])

        self.master.related.add_element(self.field_name, self.table)

        #self.gtkwidget.set_property('sensitive', True) 

    def set_value(self, value):
        self.table.set_records(value)

    def get_value(self, shown=False):
        return self.table.records 

    def prepare_label_map(self):
        """
        Implement the possibility to specify a label key as::

           related_field.field_name

        so that related field can be personalized in different ways.
        As an example a project can have tho relations to the user table, one is under
        'staff' attribute and the second via 'manager'. Bothe these point to 'username'
        that should appear in the mask with staff and manager label.
        """

        from copy import copy
        label_map = copy(self.master.label_map)

        for key, value in label_map.items():
            if key.startswith('%s.' % self.field_name):
                key = key.replace('%s.' % self.field_name, '')
                label_map[key] = value

        return label_map


def filter_related(my_dict, relation):
    """
    filters a dict to use only width info for relation 'relation'
    e.g:
    a = {'ind.cap' : 5, 'username' : 7}
    >>> filter_related(a, 'ind')
    {'cap': 5}
    """

    new = {}
    strip = '%s.' % relation
    if my_dict:
        for key in my_dict:
            if key.startswith(strip):
                nkey = re.sub('^%s' % strip, '', key)
                new[nkey] = my_dict[key]

    return new

