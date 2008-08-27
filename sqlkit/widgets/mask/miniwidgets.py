"""
Gtk Widgets
===========

widgets to be used by fields to display values and edit 

"""


class ValidationError(Exception): pass
import localtimezone
import gtk
import dbg

NOT_NULL_COLOR = gtk.gdk.color_parse('LightGoldenrod')


class Widget(object):
    def __init__(self, gtkwidget, field):
        self.gtkwidget = gtkwidget
        self.field = field
        self.master = field.master
        self.field_name = field.field_name

        if self.field.db_spec['edit']:
            if not self.field.db_spec['nullable'] or self.field.db_spec['pkey']:
                gtkwidget.modify_base(gtk.STATE_NORMAL, NOT_NULL_COLOR)

        gtkwidget.set_property('sensitive', self.field.db_spec['edit']) 

    def set_value(self, value, displayed=False):
        """if shown is True, the displayed value is returned also in any
        case. The difference is only for ForeignKey
        The displayed valu may be used for completion purpouses
        """
        pass

    def get_changed(self):
        """true if value is different from initial setting
        """
        #print "get_changed - %r: or: %r ==> %r" % (self.field_name, self.initial_value, self.get_value())
        return not self.get_value() == self.initial_value
    
    def get_value(self):
        pass

class VarcharWidget(Widget):
    #  to prevent to change NULL to '' and viceversa
    #  we store the value when setting it 
    #  and compare it wher getting

    def __init__(self, *args):

        Widget.__init__(self, *args)
        self.add_completion()

    def add_completion(self):
        """add complition bindings and liststore
        """
        self.gtkwidget.connect(
            'button-press-event', self.master.completion.pop_menu,  self.field_name, 3)
        self.gtkwidget.connect(
            'key-press-event', self.master.completion.keypress_event_cb,  self.field_name)

        self.master.completion.add_simple_completion(
            self.field_name, 'regexp', self.gtkwidget)

    def set_value(self, value):
        # Entry
        if value == None:
            value = ''
        self.initial_value = value
        self.gtkwidget.set_text( str(value) )
        
    def get_value(self, shown=False):
        value = self.gtkwidget.get_text( )
        ## don't change from None to '' 
        if value == '' and self.initial_value is None:
            return None
        return value

        
class IntegerWidget(VarcharWidget):

    def __init__(self, *args):
        Widget.__init__(self, *args)
        self.gtkwidget.set_alignment(1), self.gtkwidget
        self.gtkwidget.connect('key-press-event', self.master.digits_check_input_cb  )
                
    def set_value(self, value):
        # Entry
        if value == '':
            self.initial_value = None
        else:
            self.initial_value = value

        self.gtkwidget.set_text( str(value or '') )
        
    def get_value(self, shown=False):
        text = self.gtkwidget.get_text( )
        if text == '':
            return None
        return int(text)

class FloatWidget(IntegerWidget):

    def get_value(self, shown=False):
        text = self.gtkwidget.get_text( )
        if text == '':
            return None
        return float(text)

class DateWidget(Widget):

    def __init__(self, *args):
        Widget.__init__(self, *args)
        self.gtkwidget.set_property('show-time', False)

    def set_value(self, value):
        self.initial_value = value
        self.gtkwidget.set_property('time', value)

    def get_value(self, shown=False):
        return self.gtkwidget.get_property('time')


class TimeWidget(Widget):

    def __init__(self, *args):
        raise NotImplemented('Time Widget is not yet implemented')

class DateTimeWidget(Widget):

    def __init__(self, *args):
        Widget.__init__(self, *args)
        self.gtkwidget.set_property('show-time', True)
        
    def set_value(self, value):
        ## FIXME: datetime has only time?
        self.initial_value = value
        self.gtkwidget.set_property('time', value)

    def get_value(self, shown=False):
        time = self.gtkwidget.get_property('time')
        return time.replace(microsecond=0)

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
        self.initial_value = value


    def get_value(self, shown=False):
        value = self.gtkwidget.get_property('time')
        if not self.TZ:
            ## Local will return a tzinfo with the timezone of the system
            ## it will be added to bypass the limitaition od dateedit
            self.TZ = localtimezone.Local
            self.microsecond = 0

        if value is None:
            return None
        else:
            return value.replace(tzinfo=self.TZ, microsecond=self.microsecond)


class TextWidget(Widget):

    def set_value(self, value):
        if value is None:
            value = ''
                
        buff = self.gtkwidget.get_buffer()
        buff.set_text( value)
        self.initial_value = value

    def get_value(self, shown=False):
        buff = self.gtkwidget.get_buffer()
        ts = buff.get_iter_at_offset(0)
        te = buff.get_iter_at_offset(-1)
        text = buff.get_text(ts, te)
        return text
        

class BooleanWidget(Widget):
    """Null value is not admittable"""

    def set_value(self, value):
        if value not in (True, False):
            raise ValidationError("Null value not admittable for field '%s'" % self.field_name) 
            
        self.gtkwidget.set_active(value)
        self.initial_value = value

    def get_value(self, shown=False):
        return self.gtkwidget.get_active( )
        
class BooleanNullWidget(Widget):
    """This gtkwidget is placed in inconsinstent state to represent NULL
    """

    def set_value(self, value):
        if value not in (True, False, None):
            raise ValidationError("Null value not admissable for field %s" % self.field) 
            
        if value == None:
            self.gtkwidget.set_inconsistent(True)
        else:
            self.gtkwidget.set_active(value)
            self.gtkwidget.set_inconsistent(False)
        self.initial_value = value

    def get_value(self, shown=False):
        if self.gtkwidget.get_inconsistent():
            return None
        else:
            return self.gtkwidget.get_active( )
            

class ForeignKeyWidget(Widget):
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

        self.gtkwidget.connect('changed', self.clean_real_value)
        self.gtkwidget.set_model(self.model)
        self.gtkwidget.set_text_column(2)

        self.gtkwidget.connect(
            'button-press-event', self.master.completion.pop_menu, self.field_name, 3)
        self.gtkwidget.connect(
            'key-press-event', self.master.completion.keypress_event_cb, self.field_name)


    def clean_real_value(self, *args):
        ## the EntryText has been changed. The value may no longe be  valid
        self.real_value = False

    def set_value(self, value):
        """We have a 'real_value' that is normally an id or a key and a 'display_value'
        that is the value we want to show
        """
        self.initial_value = value
        
        display_value = self.master.completion.lookup_value(self.field.field_name, value)
        if value == None:
            if self.field.db_spec['type'] == str:
                value = ''

        self.model.clear()
        self.model.append([value, display_value, '',''])
        self.gtkwidget.set_active(0)   # which column 
#        self.real_value = True  ?????

        #self.gtkwidget.set_text( str(value) )
        
    def get_value(self, shown=False):
        #dbg.write()

        if shown == True:
            ## this is for completion. The value needed is the value in the entry not in the model
            entry = self.gtkwidget.child
            return entry.get_text()

        idx = self.gtkwidget.get_active()
        value, display_value, descr, obj_dict = self.model[idx]

        return  value

        #return self.model.get_active
            
            ## we're here if the user has written the text by hand
            ## not choosing from the list
            ## need to get the value of the id from the foreign table
            ## and cope with possible inexistend values
    #raise NotImplemented
    

        
