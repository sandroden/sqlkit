import sys, re, datetime
import config
import reflect
import layout
import validator
import dateedit
from layoutgenerator import TableLayoutGenerator
import gtk, pango
from sqlalchemy import *


class SqlMask (object):

    mwidgets = None  # mask widgets
    fields   = None  # fields to use
    
    def __init__ (self, mapper, lay = None, valid = None,
                  record = None, naked=False, table=None, mode='rw',
                  noup=None):
        """create an interface and allow to save/store data from a database

        mapper: a sqlalchemy mapper
        lay:    a layout describing the desired layout (see layout package)
        validator: a validator to be used to validate fields and records
        record: in case a mapped record from sqlalchemy
        naked:  in case the mask should *not* be added interactive buttons
                neede if the layout already contains all the required buttons
        mode:   ro|rw. When in read-only no save/delete is alllowed
        noup:   list of field-name that cannot be updated
        """
        
        self.table = table
        self.mapper = mapper
        ##  types are written in mapped records bettere than in sqlalchemy Tables
        if not record:
            self.fake_record
            record = self._get_one_record()
        else:
            self.fake_record = False
            
        self.record = record
        if not valid:
            valid = validator.Validator()
        self.valid = valid
        self._analize_record_for_types()

        ## layout
        if lay is None:
            gen = TableLayoutGenerator (self.table, naked=naked)
            self.layout = gen.layout
        else:
            self.layout = lay

        ## add default buttons if needed
        self._add_default_buttons(naked)

        ## create the interface and add obvious constraints
        self.lay_obj = layout.Layout (self.layout)
        self.lay_obj.prop('Window', 'visible', False)
        self.w       = self.lay_obj.show()
        self._analize_widgets_in_layout()
        self._add_constraints()
        self._add_actions_to_buttons()
        self._fill_menubar_menu()

        ## fill in the data in case
        if record:
            self.record_display(record)
        ## only render when dimentions are complete
        self.w['Window'].show()
        
    def record_display(self, mapped_record):
        """display a mapped record in the mask
        """
        if self.fake_record:
            #print "record_display: no record"
            self.fake_record = False
            return
        ## fill in the data
        #print "record_display"
        for field_name in self.fields.keys():
            field_value = getattr(self.record, field_name)
            #print "record_display: %s %s", (field_name, type(field_value))
            self._set_value(field_name, field_value)

    def _set_value(self, field_name, field_value):
        # this is the method that knows how to handle different type of data
        # [0]: the gtkClass
        # [1]: the gtkWidget
        widget = self.mwidgets[field_name][1]
        
        # Entry
        if isinstance (widget, gtk.Entry):
            widget.set_text( str(field_value) )
        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            widget.set_property('time', field_value)

        # Boolean
        elif isinstance (field_value, bool):
            widget.set_active(field_value)
        
    def _get_value(self, field_name, field_value):
        # this is the method that knows how to handle different type of data
        # [0]: the gtkClass
        # [1]: the gtkWidget
        widget = self.mwidgets[field_name][1]
        
        # Entry
        if isinstance (widget, gtk.Entry):
            return widget.get_text( )

        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            widget.get_property('time')

        # Boolean
        elif isinstance (field_value, bool):
            widget.get_active( )
        
    def record_delete(self):
        """ function that invokes the validator before DELETing a record"""
        ## FIXME: validator
        objectstore.delete (self.record)
        objectstore.commit ()

    def record_save(self):
        """ function that invokes the validator before UPDATE/INSERT a record"""
        ## FIXME: validator
        ## FIXME: passare da table -> mapper

        if self.validator is not None:
            v = self.validator (self.table, record)
            v.validate ()
      
        objectstore.commit ()

    def record_new(self):
        """clear the mask for a new record"""
        pass

    def _analize_record_for_types(self):
        """fill 'fields' dictionary analizing types

        fields:  dict to store fields that appear in layout. Good for loops
        key: field_name  value: type
        """

        self.fields = {}
        for field_name in self.mapper.c.keys():
            field_value = getattr(self.record, field_name)
            print field_name, type(field_value)
            self.fields[field_name] = type(field_value)
        
        
    def _analize_widgets_in_layout(self):
        """fill variables from layout

        mwidgets: dict to store mask widgets
                 key: field_name  value: ( gtkClass, widgetName )
        """
        ## FIXME: does not work when renaming: euro.user_id -> euro_user_id

        self.mwidgets = {}
        ## by now I only use entry, date, radio and menu to represent data
        #print self.w.keys()
        for field_name in self.fields.keys():
            #print "_analize_widget_layout: %s" % (field_name)
            for mod in ('e','d','r','m','c'):
                try:
                    widget = self.w["%s=%s" % (mod, field_name)]
                except:
                    pass
            # (gtkClass , gtkWidget)
            self.mwidgets[field_name] = (type(widget), widget)
        
    def _add_default_buttons (self, naked=False):
        # a 'neked' mask is a mask w/o buttons. Maybe buttons are define by the
        # programmer inside the layout, maybe are not desired
        if not naked:
            self.layout = """
            {B m=file m=modifica m=opzioni m=aiuto}
            {O tb=gtk-save tb=gtk-delete tb=gtk-new tb=gtk-refresh tb=gtk-quit}
            { %s}
            """ % (self.layout)
    
    def _fill_menubar_menu(self):
        """here all menus are filled for filtering,  sorting, ro, query..."""
        if 'm=file' in self.w:
            self.lay_obj.menu('m=file',
                              ('gtk-quit', self.quit)
                              )

    def _get_one_record(self):
        # it's just here to study the types, not to be represented
        self.fake_record = True
        return self.mapper.select(limit=1)[0]
        
    def _add_constraints(self):
        """Add controls according to data type represented """
        
        for field_name in self.fields.keys():
            field_type = self.fields[field_name]
            widget = self.mwidgets[field_name][1]

            ## integer
            if field_type == int:
                # left justified
                widget.set_alignment(1)
                # check the input
                widget.connect('key_press_event', self.digits_check_input  )
                
            ## Strings
            if field_type == str:
                # max N. of char
                #widget.set_max_length()
                ## FIXME: may I get it from mapper instead of Table?
#         if isinstance (column.type, types.String) and column.type.length is not None:
#             self.w [column_layout].set_max_length (column.type.length)
                pass

            ## Dates / Datetime
            if field_type == datetime.date:
                widget.set_property('show-time', False)
            elif field_type == datetime.datetime:
                widget.set_property('show-time', True)
                
            widget.connect('focus-out-event',self.leave_widget)
            
    def leave_widget(self, widget, more):
        print "leave_widget: ", widget, more

    def quit(self, widget):
        """Quit operations: check is need to save first """
        ### fixme: must add cheks
        ### fixme2: must the toplevel be destrouyed (or is reparented?)
        print widget
        self.w['Window'].destroy()

    
    def _add_actions_to_buttons(self):
        """ Add default actions to std buttons"""
        actions = {
            ## std toolbutton
            'tb=gtk-save'    : self.record_save,
            'tb=gtk-new '    : self.record_new,
            'tb=gtk-delete'  : self.record_delete,
            'tb=gtk-refresh' : self.record_save,
            'tb=gtk-quit'    : self.quit,

            ## in case the programmers has set them
            'b=gtk-save'    : self.record_save,
            'b=gtk-new '    : self.record_new,
            'b=gtk-delete'  : self.record_delete,
            'b=gtk-refresh' : self.record_save,
            'b=gtk-quit'    : self.quit,
            }
        for widget_name, handler in actions.iteritems():
            if widget_name in self.w:
                #print "_add_actions_to_button: %s %s %s" % (
                #    widget_name, 'clicked', handler)
                self.w[widget_name].connect('clicked', handler)

    def digits_check_input(self, widget, event):
        ## fixme: missing comma, and cut&paste
        key = gtk.gdk.keyval_name (event.keyval)
        print key
        if not re.match ('([0-9.,]|BackSpace|Left|Right)', key):
            return True

