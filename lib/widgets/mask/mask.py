import sys, re, datetime
#import config
import inspect
#import common
import layout
import layout.dateedit as dateedit

#import validator
from layoutgenerator import TableLayoutGenerator
import gtk, pango
from sqlalchemy import *
import dbg.gtk_dbg
import sqlkit.sqlfilter as sqlfilter
import sqlkit.sqldata as sqldata
import sqlkit.inspect as inspect
import sqlkit.validator as validator
import sqlkit.parseopts as parseopts
import sqlkit.completion as completion

#NOT_NULL_COLOR = gtk.gdk.color_parse('yellow')
NOT_NULL_COLOR = gtk.gdk.color_parse('LightGoldenrod')
FK_COLOR = gtk.gdk.color_parse('navyblue')
LBL_HOOVER_STYLE = gtk.gdk.color_parse('red')

class SqlMask (object):
    """doc string for sqlmask
    """
    mwidgets = None  # mask widgets: key: field_name  value: ( gtkClass, widgetName )
    fields   = None  # fields to use (InspectMapper)
    labels   = None  # correspondance Label <-> EventBox
#    map_record_n = 0  # number of the displayed record within mapper
    row_count = 0    # number of records in the mapper
    tables = None    # Table objects referenced as foreign keys
    values = None    # real value for foreign key (when lookup is displeyed instead)
    def __init__ (self, mapper=None,
                  lay = None,
                  valid = None,
#                  records = None,
                  naked=False,
                  table=None,
                  tables=None,
                  mode='rw',
                  noup=None,
                  sql=None,
                  constraint=None,
                  engine=None,
                  title=None,
                  order_by=None
                  ):
        """create an interface and allow to save/store data from a database

        mapper: a sqlalchemy mapper
        lay:    a layout describing the desired layout (see layout package)
        validator: a validator to be used to validate fields and records
        naked:  in case the mask should *not* be added interactive buttons
                neede if the layout already contains all the required buttons
        mode:   ro|rw. When in read-only no save/delete is alllowed
        noup:   list of field-name that cannot be updated
        """
        
        if engine:
            self.engine = engine
        self.order_by = order_by
        ## we can use singular or plural as an option, plural in the code
        if table and not tables:
            tables = table
        self.mapper = parseopts.get_mapper(self, mapper, tables)
        if not engine:
            self.engine = self.mapper.table.engine
        self.valid = self._get_validator(valid)
        self.fields = parseopts.inspect_mapper(self.mapper, noup=noup, mode=mode)
        self.title = self._get_title(title)
#        self.tables = {}
        self.values = {}
        self.completion = completion.Completion(self, )
        ## create the interface and add obvious constraints
        self.lay_obj, self.w  = self._get_layout(lay, naked)
        ## fill in the data in case
#         if records:
#             dbg.write('ora self.record_display, records: ' % records)
#             self.record_display()
        if sql:
            #dbg.write('__init__ sql: %s' % sql)
            self.reload(sql)
            
        ## only render when dimentions are complete
        self.w['Window'].show()

####### Record browsing & saving
    def record_display(self, record=None, incr=0):
        """display a mapped record in the mask

        display the data provided by self.sqlData.get()
        incr: incr=incr arg to sqlData.get()
        """
        #dbg.write('Record_display n: %s' % self.sqlData.index())
        ## fill in the data
        #self.record_clear()
        try:
            data_in = self.sqlData.get(incr=incr)
        except:
            self.sb("no data to browse")
            return
        #dbg.write("data_in", data_in)
        msg_info = "record %s/%s" % (self.sqlData.index()+1, self.sqlData.count())
        if not data_in:
            if incr > 0:
                self.lay_obj.sb('Already last ' + msg_info)
            else:
                self.lay_obj.sb('Already first ' + msg_info)
            return
        self.record_clear()
        
        self.sb(msg_info)
        self.data_in = data_in
        for field_name, value in data_in.iteritems():
            self._set_value(field_name, value)
        self.status = self.sqlData.get_current()
        
    def _set_value(self, field_name, field_value):
        """this is the method that knows how to handle different type of data
        if field_name is a FKey ending with _id, it retrieves the description,
        shows it in the entry but stores the id in self.values[field_name]
        """
        #dbg.write("%s: %s" % (field_name, field_value))
        # [0]: the gtkClass
        # [1]: the gtkWidget
        if field_name not in self.mwidgets:
            return
        widget = self.mwidgets[field_name][1]

        if self.fields[field_name]['fkey'] and field_name.endswith('_id'):
            self.values[field_name] = field_value
            field_value = self.completion._lookup_value(field_name, field_value)
            

        #dbg.write( "name: %s type: %s" % ( field_name, self.fields[field_name] ))
        # Entry
        if isinstance (widget, gtk.Entry):
            if field_value == None:
                field_value = ''
            widget.set_text( str(field_value) )
        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            widget.set_property('time', field_value)

        # Boolean
        elif self.fields[field_name]['type'] == bool:
            if not field_value :
#                 dbg.write("impongo false per %s che era '%s'" % (
#                     field_name, field_value))
                field_value = False
            widget.set_active(field_value)
            #dbg.write("%s: %s" % (field_value, widget.get_active()))
        
    def _get_value(self, field_name):
        """return the data for field_name
        in case self.values[field_name] exists, it gets that value instead
        """
        # [0]: the gtkClass
        # [1]: the gtkWidget
        if field_name not in self.mwidgets:
            raise FieldNotInLayout
        
        widget = self.mwidgets[field_name][1]

        ## give a try if we have stored a value
        try:
            return self.values[field_name]
        except:
            pass
        
        # Entry
        if isinstance (widget, gtk.Entry):
            text = widget.get_text( )
            if text == '':
                if self.fields[field_name]['type'] == int:
                    return None
            return text

        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            return widget.get_property('time')

        # Boolean
        elif self.fields[field_name]['type'] == bool:
            return widget.get_active( )

    def record_delete(self, widget=None):
        """invokes the validator before DELETing a record"""
        ## FIXME: validator
        self.sqlData.delete()
        #dbg.write(objectstore.commit())
        self.engine.echo = True
        objectstore.commit()
        self.engine.echo = False
        #dbg.write(self.record_clear())
        self.record_clear()
    
    def record_save(self, ev):
        """invokes the validator before UPDATE/INSERT a record"""
        ## FIXME: validator
        ## FIXME: passare da table -> mapper
    
        
        #         if self.valid is not None:
        #             v = self.valid (self.table, record)
        #             v.validate ()

        if not self.status:
            self.record_save_new()
            return
    
        R = {}
        for field_name in self.fields.keys():      
            try:
                value = self._get_value(field_name)
            except FieldNotInLayout:
                continue
            #dbg.write(field_name, value)
            
            t = self.fields[field_name]['type']
            #dbg.write("%s: - value: %r T: %s" % (field_name, value, t))
            if t == datetime.date:
                if value is not None:
                    value = t(value.year, value.month, value.day)
            elif t == datetime.datetime:
                if value is not None:
                    value = t(value.year, value.month, value.day,
                              value.hour, value.minute, value.second)
            else:
                if value is not None:
                    #dbg.write("value is", value)
                    value = t(value)

            if value != self.data_in[field_name]:
               if value == '' and self.data_in[field_name] == None:
                   pass
               else:
                   #dbg.write("%s: %r is not %r" % (field_name,
                   #                                value, self.data_in[field_name]))
                   R[field_name] = value

        #dbg.write(R)
        if R.keys():
            self.sqlData.set(R)
            
        self.engine.echo = True
        objectstore.commit ()
        self.engine.echo = False
        
    def record_save_new(self):
        """Insert a new record
        """
        
        R = {}
        for field_name in self.fields.keys():      
            try:
                value = self._get_value(field_name)
            except FieldNotInLayout:
                continue
            
            t = self.fields[field_name]['type']
            if t == int and value == '':
                # skip type casting
                R[field_name] = None
                continue
            #dbg.write("%s: - value: %r t: %s" % (field_name, value, t))
            if t == datetime.date:
                value = t(value.year, value.month, value.day)
            elif t == datetime.datetime:
                value = t(value.year, value.month, value.day,
                          value.hour, value.minute, value.second)
            else:
                if value is not None:
                    value = t(value)
                
#             if self.fields[field_name]['is_serial'] and not value:
#                 value = self.next_serial(field_name)
            R[field_name] = value

        #dbg.write(R)
        self.sqlData.add(R)
        self.status = self.sqlData.get_current()
        dbg.write("self.status", self.status)

        objectstore.commit ()
        self.record_display()
        
    def record_clear(self, widget=None):
        """clear the mask for a new record"""
        #dbg.write('')
        self.values.clear()
        self.status = None
        self.sb("New Record")
        
        for field_name in self.fields.keys():
            #dbg.write(field_name)
            self._set_value(field_name, '')
    def record_forward(self, ev):
        """display the next record in the mapper"""
        self.record_display(incr=1)
        
    def record_back(self, ev):
        """display the previous record in the mapper"""
        self.record_display(incr=-1)
    def reload(self, sql=None, params=None, limit=100):
        """reload data from db

        sql may be a tuple (sql_statement, bind_params) or just a sql_statement
        """
        #dbg.write(sql)
        if isinstance(sql, tuple) and len(sql) == 2:
            sql_str, params = sql
            #dbg.write('type sql_str', type(sql_str), 'type params', type(params))
            #dbg.sql_debug(sql_str, params)
        else:
            sql_str = sql
            params = None
        #dbg.write("SQL", sql_str, 'params', params)
        #self.mapper.table.engine.echo = True
        records = self.mapper.select(sql_str, params=params, order_by=self.order_by)
        #records = self.mapper.select_by(sql)
        #self.mapper.table.engine.echo = False
        self.sqlData = sqldata.SqlData(records, mapper_info=self.fields)
        self.record_display()
    
    def reload_cb(self, widget):
        """issue a reload operation on master. Call back of reload button"""
        #limit=100
        self.reload( )

    

####### Layout, Reflection & Analisys
    def _get_validator(self, valid):
        if not valid:
            valid = validator.Validator()
        self.valid = valid
    def _get_layout(self, lay, naked):
        ## layout
        lay = TableLayoutGenerator(self.fields, naked=naked, lay=lay).layout

        self.layout = lay
        self.add_filter(visible=False)

        ## add default buttons if needed
        #self._add_default_buttons(naked)
        #dbg.write(self.layout)
        self.lay_obj = layout.Layout(self.layout, title=self.title, opts='T-')
        self.lay_obj.prop('Window', 'visible', False)
        self.w       = self.lay_obj.show()
        self._analize_widgets_in_layout()
        self._add_constraints_and_connect()
        self._add_actions_to_buttons()
        self._add_colors_and_fonts()
        self._fill_menubar_menu()
        return (self.lay_obj, self.w)
    
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
            #dbg.write("_analize_widget_layout: %s" % (field_name))
            for mod in ('e','d','r','m','c'):
                try:
                    widget = self.w["%s=%s" % (mod, field_name)]
                    self.mwidgets[field_name] = (type(widget), widget)
                except:
                    pass
            # (gtkClass , gtkWidget)

        ## all EventBox 
        #dbg.write("self.w: %s" % self.w)
        #dbg.dshow(self.w, 'E=')
        self.labels = {}
        #dbg.write(self.fields.keys())
        for field_name in self.fields.keys():
            lbl_name_wdg = "l=%s" % field_name
            if lbl_name_wdg in self.w:
                self.labels[field_name] = self.w[lbl_name_wdg]
                #dbg.write("%s -> %s"% (field_name, self.labels[field_name]))
            else:
                #dbg.write("Missing event_box for %s" % (field_name))
                pass
            
    def _fill_menubar_menu(self):
        """here all menus are filled for filtering,  sorting, ro, query..."""
        if 'm=file' in self.w:
            self.lay_obj.menu('m=file',
                              ('filter panel', self.add_filter),
                              ('-', None),
                              ('inspect', self.show_mapper_info),
                              ('-', None),
                              ('gtk-quit', self.quit)
                              )
    
    def _add_colors_and_fonts(self):
        """add bg colors and onts to signal needed fields"""

        for field_name in self.fields.keys():
            if field_name in self.mwidgets:
                if not self.fields[field_name]['nullable'] or \
                       self.fields[field_name]['pkey'] :
                    wdg_type, wdg = self.mwidgets[field_name]
                    wdg.modify_base(gtk.STATE_NORMAL, NOT_NULL_COLOR)

        for field_name in self.fields.keys():
            if field_name in self.labels:
                lbl    = self.labels[field_name]
                ev_wdg = self.labels[field_name].parent
                ev_wdg.connect('enter-notify-event', self.ene_cb)
                ev_wdg.connect('leave-notify-event', self.lne_cb)
                lbl.modify_fg(gtk.STATE_PRELIGHT, LBL_HOOVER_STYLE)

                ## label FK_COLOR to tell it's a foreign key
                if self.fields[field_name]['fkey'] :
                    #dbg.write("FK", field_name)
                    self.labels[field_name].modify_fg(gtk.STATE_NORMAL, FK_COLOR)
                else:
                    #dbg.write("NO", field_name)
                    pass
            
    def ene_cb(self, eb, ev):
        eb.get_child().set_state(gtk.STATE_PRELIGHT)
        return True
    def lne_cb(self, eb, ev):
        eb.get_child().set_state(gtk.STATE_NORMAL)
        return True
        
    def _add_constraints_and_connect(self):
        """Add controls according to data type represented
        check on input for integers
        configuring date / datetime for time*
        adding focus-out staff
        adding tooltips and click for filter_panel
        """
        for field_name in self.fields.keys():
            field_type = self.fields[field_name]['type']
            ## the widget may not be there, is layout has been provided
            ## as an argument
            if field_name not in self.mwidgets:
                #dbg.write("skip %s" % field_name)
                continue
            widget = self.mwidgets[field_name][1]
            if not widget:
                #dbg.write("Per campo: %s manca widget %s" % (field_name, widget))
                continue
            
            ## integer
            if field_type == int and not self.fields[field_name]['fkey']:
                # left justified
                #print "field_name:", field_name
                widget.set_alignment(1), widget
                # check the input
                widget.connect('key-press-event', self.digits_check_input  )
                
            ## Strings
            if field_type == str or self.fields[field_name]['fkey']:
                #dbg.write("aggiungo <3> per %s" % (field_name))
                widget.connect('button-press-event',self.completion.pop_menu,
                               field_name, 3)
                widget.connect('key-press-event',
                               self.completion.entry_short_cut_event,
                               field_name, 'F1')
#             else:
#                 dbg.write("fkey per %s: %s" %
#                          (field_name, self.fields[field_name]['fkey']))
            ## Dates / Datetime
            if field_type == datetime.date:
                widget.set_property('show-time', False)
            elif field_type == datetime.datetime:
                widget.set_property('show-time', True)
                
            #widget.connect('focus-out-event',self.focus_out__widget, field_name)
            #widget.connect('focus-in-event',self.focus_in__widget)
            try:
                widget.connect('activate',self.on_activate_cb, field_name)
            except:
                # FIX? dateedit don't have 'activate'
                pass

        ## add click that pops filter_panel
        for field_name, label in self.labels.iteritems():
            #dbg.write("<1> x filter: %s %s" % (field_name, event_box))
            event_box = label.parent
            event_box.connect('button-press-event',
                              self.filter_panel.add, field_name, 1)

        # key accelerators
        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_group(ord('h'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.show_widgets)
        self.accel_group.connect_group(ord('q'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.gquit)
        self.w['Window'].add_accel_group(self.accel_group)
            
            
    def _add_actions_to_buttons(self):
        """ Add default actions to std buttons"""
        actions = {
            ## std toolbutton
            'tb=gtk-save'       : self.record_save,
            'tb=gtk-new'        : self.record_clear,
            'tb=gtk-delete'     : self.record_delete,
            'tb=gtk-refresh'    : self.reload_cb,
            'tb=gtk-quit'       : self.quit,
            'tb=gtk-go-forward' : self.record_forward,
            'tb=gtk-go-back'    : self.record_back,

            ## in case the programmers has set them
            'b=gtk-save'       : self.record_save,
            'b=gtk-new'        : self.record_clear,
            'b=gtk-delete'     : self.record_delete,
            'b=gtk-refresh'    : self.reload_cb,
            'b=gtk-quit'       : self.quit,
            'b=gtk-go-forward' : self.record_forward,
            'b=gtk-go-back'    : self.record_back,
            }
        for widget_name, handler in actions.iteritems():
            if widget_name in self.w:
                #print "_add_actions_to_button: %s %s %s" % (
                #    widget_name, 'clicked', handler)
                self.w[widget_name].connect('clicked', handler)
                self.lay_obj.tooltips.set_tip(self.w[widget_name], "mmh")
                self.lay_obj.tip(widget_name, "mi chiamo %s" % widget_name)

        ## style for toolbar if any
        if 'O.tool' in self.w:
            self.w['O.tool'].set_show_arrow(False)
            self.lay_obj.prop('O.tool', 'toolbar_style','GTK_TOOLBAR_ICONS')
####### Validation
    def focus_out__widget(self, widget, event, field_name):
        self.last_visited_field = field_name
        #print "focus_out", event, field_name
        
    def focus_in__widget(self, widget, event, more=None):
        #print "focus_in"
        #print "more: ",more
        pass
    
    def on_activate_cb(self, widget, field_name):
        #print self._get_value(field_name)
        self.select()
    def select(self):
        pass
    def digits_check_input(self, widget, event):
        ## fixme: missing comma, and cut&paste
        key = gtk.gdk.keyval_name (event.keyval)
        #dbg.write(key)
        ONLYDIGITS="([0-9.,]|BackSpace|Left|Right|F1|period|Tab|Up|Down)"
        if not re.match (ONLYDIGITS, key):
            dbg.write("key: %s" % key)
            return True
    
####### Misc
    def quit(self, widget):
        """Quit operations: check if need to save first """
        ### fixme: must add cheks
        ### fixme2: must the toplevel be destrouyed (or is reparented?)
        #print widget
        self.w['Window'].destroy()
        self.filter_panel.destroy()
        
    def gquit(self, *args):
        gtk.main_quit()
                       
    def sb(self, text):
        """write on the status bar, if present"""
        try:
            self.lay_obj.sb(text)
        except:
            pass
    
    def _get_title(self, title=None):
        if not title:
            try:
                title=self.table
            except:
                title= self.mapper.table.name
        return title
    
    def add_filter(self, event=None, visible=True):
        """Pop a Filter Panel"""
        try:
            self.filter_panel.w['Window'].set_property('visible', True)
            #print "add_filter: esisteva"
        except:
            self.filter_panel = sqlfilter.FilterPanel(self, visible=visible)
            #print "add_filter: mancava"
            #return sqlfilter.FilterPanel(self)
        return self.filter_panel
    
    #filter_panel = property(add_filter)
            
    
    def show_mapper_info(self, *args):
        dbg.gtk_dbg.ShowMapperInfo(self.fields)        
        
    def show_widgets(self, *args):
        import dbg.gtk_dbg
        dbg.gtk_dbg.show_widgets(self.w['Window'])
    
