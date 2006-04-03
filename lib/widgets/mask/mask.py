import sys, re, datetime
import config
import reflect
import layout
import validator
import dateedit
from layoutgenerator import TableLayoutGenerator
import gtk, pango
from sqlalchemy import *
import sqlfilter

class SqlMask (object):
    """doc string for sqlmask
    """
    mwidgets = None  # mask widgets: key: field_name  value: ( gtkClass, widgetName )
    fields   = None  # fields to use
    labels   = None  # correspondance Label <-> EventBox
    map_record_n = 0  # number of the displayed record within mapper
    row_count = 0    # number of records in the mapper
    
    def __init__ (self, mapper,
                  lay = None,
                  valid = None,
                  records = None,
                  naked=False,
                  table=None,
                  mode='rw',
                  noup=None,
                  debug=0,
                  sql=None,
                  constraint=None
                  ):
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
        self.debug = debug
        self.listores = {}
        ##  types are written in mapped records bettere than in sqlalchemy Tables
        if not records:
            self.dbg('not records')
            self.fake_record = True
            self.records = [ self._get_one_record() ]
        else:
            self.fake_record = False
            self.records = records

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
        self.add_filter(visible=False)
        
        ## add default buttons if needed
        self._add_default_buttons(naked)

        ## create the interface and add obvious constraints
        self.lay_obj = layout.Layout (self.layout)
        self.lay_obj.prop('Window', 'visible', False)
        self.w       = self.lay_obj.show()
        self._analize_widgets_in_layout()
        self._add_constraints_and_connect()
        self._add_actions_to_buttons()
        self._fill_menubar_menu()

        ## fill in the data in case
        if records:
            self.dbg('ora self.record_display, records: ' % records)
            self.record_display()
        elif sql:
            self.dbg('sql: %s' % sql)
            self.reload(sql)
            
        ## only render when dimentions are complete
        self.w['Window'].show()
        #self.add_filter('junk')
        #self.filter_panel.add('wdg', 'ev', 'field_name')
####### Record browsing & saving
    def record_display(self, record=None, next=0):
        """display a mapped record in the mask

        If a record is passed it displays that record, if not self.records is
        analized: if it has self.records[self.map_record_n], that one is displayed
        next: next is added to self.map_record_n (may be negative) and that element is displayed
        """
        self.dbg('Record_display n: %s' % self.map_record_n)
        if self.fake_record and not sql:
            ## A faked record is only retrieved to work out the types of the fields
            self.fake_record = False
            return
        ## fill in the data

        if not record:
            #self.dbg('Record_display, not record')
            n = self.map_record_n + next
            if n < 0:
                self.dbg('n = %s... esco' % n)
                return
            try:
                record = self.records[n]
                self.map_record_n += next
            except:
                #self.dbg('manca records[%s]' % n)
                return

            self.sb("record %s/%s" % (self.map_record_n, self.row_count))

        for field_name in self.fields.keys():
            field_value = getattr(record, field_name)
            #print "record_display: %s %s", (field_name, type(field_value))
            self._set_value(field_name, field_value)
    
    def _set_value(self, field_name, field_value):
        # this is the method that knows how to handle different type of data
        # [0]: the gtkClass
        # [1]: the gtkWidget
        widget = self.mwidgets[field_name][1]
        #print "name: %s type: %s" % ( field_name, self.fields[field_name] )
        # Entry
        if isinstance (widget, gtk.Entry):
            widget.set_text( str(field_value) )
        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            if field_value == '':
                return
            widget.set_property('time', field_value)

        # Boolean
        elif isinstance (self.fields[field_name], bool):
            if field_value == '':
                field_value = False
            widget.set_active(field_value)
            print widget.get_active()
        
    def _get_value(self, field_name):
        # this is the method that knows how to handle different type of data
        # [0]: the gtkClass
        # [1]: the gtkWidget
        widget = self.mwidgets[field_name][1]
        
        # Entry
        if isinstance (widget, gtk.Entry):
            return widget.get_text( )

        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            return widget.get_property('time')

        # Boolean
        elif isinstance (fields[field_name], bool):
            return widget.get_active( )
        
    def record_delete(self):
        """invokes the validator before DELETing a record"""
        ## FIXME: validator
        objectstore.delete (self.record)
        objectstore.commit ()
    
    def record_save(self, ev):
        """ invokes the validator before UPDATE/INSERT a record"""
        ## FIXME: validator
        ## FIXME: passare da table -> mapper
    
#         if self.valid is not None:
#             v = self.valid (self.table, record)
#             v.validate ()
      
        objectstore.commit ()
    
    def record_new(self, widget):
        """clear the mask for a new record"""
        print 'record_new'
        for field_name in self.fields.keys():
            self._set_value(field_name, '')
    def record_forward(self, ev):
        """display the next record in the mapper"""
        self.record_display(next=1)
        
    def record_back(self, ev):
        """display the previous record in the mapper"""
        self.record_display(next=-1)
    def reload(self, sql=None, params=None, limit=100):
        """reload data from db

        sql may be a tuple (sql_statement, bind_params) or just a sql_statement
        """
        
        if isinstance(sql, tuple) and len(sql) == 2:
            sql_str, params = sql
        else:
            sql_str = sql
            params = None
            
        self.records = self.mapper.select(sql_str, params=params, limit=limit)
        self.map_record_n = 0
        self.record_display()
        n = 0
        for i in self.records:
            n+=1
        self.row_count = n
        self.sb("Total n. of records: %s" % n)
####### Reflection & Analisys
    def _get_one_record(self):
        # it's just here to study the types, not to be represented
        self.fake_record = True
        #self.dbg(self.mapper.select(limit=1)[0])
        return self.mapper.select(limit=1)[0]
        
    def _analize_record_for_types(self):
        """fill 'fields' dictionary analizing types

        fields:  dict to store fields that appear in layout. Good for loops
        key: field_name  value: type
        """

        self.fields = {}
        for field_name in self.mapper.c.keys():
            field_value = getattr(self.records[0], field_name)
            print field_name, type(field_value), field_value
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

        ## all EventBox 
        self.labels = {}
        for field_name in self.fields.keys():
            lbl_name_wdg = "E=%s" % field_name
            if lbl_name_wdg in self.w:
                self.labels[field_name] = self.w[lbl_name_wdg]

                
    def _add_default_buttons (self, naked=False):
        # a 'naked' mask is a mask w/o buttons. Maybe buttons are define by the
        # programmer inside the layout, maybe are not desired
        if not naked:
            self.layout = """
            {B m=file m=modifica m=opzioni m=aiuto}
            {O.tool tb=gtk-save tb=gtk-delete tb=gtk-new tb=gtk-refresh tb=gtk-quit
               tb=gtk-go-back tb=gtk-go-forward}
            { %s}
            sb=StBar
            """ % (self.layout)
    
    def _fill_menubar_menu(self):
        """here all menus are filled for filtering,  sorting, ro, query..."""
        if 'm=file' in self.w:
            self.lay_obj.menu('m=file',
                              ('filter panel', self.add_filter),
                              ('-', None),
                              ('gtk-quit', self.quit)
                              )
    def _add_constraints_and_connect(self):
        """Add controls according to data type represented
        check on input for integers
        configuring date / datetime for time*
        adding focus-out staff
        adding tooltips and click for filter_panel
        """
        
        for field_name in self.fields.keys():
            field_type = self.fields[field_name]
            widget = self.mwidgets[field_name][1]
            print field_name, widget

            ## integer
            if field_type == int:
                # left justified
                print "field_name:", field_name
                widget.set_alignment(1), widget
                # check the input
                widget.connect('key-press-event', self.digits_check_input  )
                
            ## Strings
            if field_type == str:
                # max N. of char
                #widget.set_max_length()
                ## FIXME: may I get it from mapper instead of Table?
#         if isinstance (column.type, types.String) and column.type.length is not None:
#             self.w [column_layout].set_max_length (column.type.length)
                widget.connect('button-press-event',self.pop_menu, field_name, 3)

            ## Dates / Datetime
            if field_type == datetime.date:
                widget.set_property('show-time', False)
            elif field_type == datetime.datetime:
                widget.set_property('show-time', True)
                
            widget.connect('focus-out-event',self.focus_out__widget, field_name)
            widget.connect('focus-in-event',self.focus_in__widget)
            try:
                widget.connect('activate',self.on_activate_cb, field_name)
            except:
                # FIX? dateedit don't have 'activate'
                pass

        ## add click that pops filter_panel
        for field_name, event_box in self.labels.iteritems():
            event_box.connect('button-press-event',
                              self.filter_panel.add, field_name, 1)
            
            
    def _add_actions_to_buttons(self):
        """ Add default actions to std buttons"""
        actions = {
            ## std toolbutton
            'tb=gtk-save'       : self.record_save,
            'tb=gtk-new'        : self.record_new,
            'tb=gtk-delete'     : self.record_delete,
            'tb=gtk-refresh'    : self.record_save,
            'tb=gtk-quit'       : self.quit,
            'tb=gtk-go-forward' : self.record_forward,
            'tb=gtk-go-back'    : self.record_back,

            ## in case the programmers has set them
            'b=gtk-save'       : self.record_save,
            'b=gtk-new'        : self.record_new,
            'b=gtk-delete'     : self.record_delete,
            'b=gtk-refresh'    : self.record_save,
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
        print self._get_value(field_name)
        self.select()
    def select(self):
        pass
    def digits_check_input(self, widget, event):
        ## fixme: missing comma, and cut&paste
        key = gtk.gdk.keyval_name (event.keyval)
        print key
        if not re.match ('([0-9.,]|BackSpace|Left|Right)', key):
            return True
    
####### Misc
    def quit(self, widget):
        """Quit operations: check if need to save first """
        ### fixme: must add cheks
        ### fixme2: must the toplevel be destrouyed (or is reparented?)
        print widget
        self.w['Window'].destroy()
        self.filter_panel.destroy()
        
    def sb(self, text):
        """write on the status bar, if present"""
        try:
            self.lay_obj.sb(text)
        except:
            pass
    
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
            
    def dbg(self, text):
        if self.debug == 1:
            print text
    
####### Completion
    def add_completion(self, field_name, mode):
        """ add a completionEntry to an Entry
        return a listore to be filled
        """

        entry = self.mwidgets[field_name][1]
        completion = entry.get_completion()
        if completion:
            completion.set_match_func(self.match_func, (0, mode))
            return (completion.get_model(), completion)

        ## completion was not present
        completion = gtk.EntryCompletion()
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)
        completion.set_match_func(self.match_func, (0, mode))
            
        listore = gtk.ListStore(str)
        self.listores[field_name] =  listore
        if mode == 'regexp':
            completion.insert_action_text(1,'start with...')
        else:
            completion.insert_action_text(2,'regexp')

        completion.set_model(listore)
        completion.set_inline_completion(True)
        entry.set_completion(completion)
        completion.set_text_column(0)
        return (listore, completion)
    def match_func(self, completion, key, iter, func_data):
        column, mode = func_data
        model = completion.get_model()
        text = model.get_value(iter, column)
        if not text:
            text = ''
        #return False
        # start
        if mode == 'start':
            if text.startswith(key):
                return True
            else:
                return False
        # regexp
        if re.search(key, text):
            return True
        return False
    def show_field_info(self, wdg, ev):
        pass
    def show_possible_values(self, wdg, field_name, mode):
        """fill in a ListStore to use with completion, fetch data from db
        mode determines the match of the already typed text:
        start: only matching data starting with typed text
        regexp: typed text is a regexp (*~ or ILIKE)
        all: all values
        """
        print "show_possible_values %s" % field_name
        val = self.mwidgets[field_name][1].get_text()
        if mode == 'start':
            oper = 'ILIKE'
            val += '%'
        if mode == 'regexp':
            oper = '~*'
        else:
            oper = '~'
            val = "."
            
        sql = "%s %s :%s" % (field_name, oper, field_name)
        listore, completion = self.add_completion(field_name, mode)
        listore.clear()
        ret = self.mapper.select(sql, params={field_name : val})
        for R in ret:
            listore.append([getattr(R, field_name)])
        completion.complete()
        
    def pop_menu(self, wdg, ev, field_name, num_button):
        #print "pop_menu", wdg, ev
        if not ev.button == num_button:
            return False

        print ev.button
        try:
            self.w['M=popup'].destroy()
        except:
            pass

        
        self.w['M=popup'] = gtk.Menu()
        menu = self.w['M=popup']
        ## info on field
        item = gtk.MenuItem(label="info on %s" % field_name.replace('_','__'))
        item.connect('activate', self.show_field_info, field_name)
        label = "Show all info on this field, db type and such"
        self.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)
        
#         ## possible values
#         item = gtk.MenuItem(label="possible values")
#         item.connect('activate', self.show_possible_values, field_name, 'all')
#         label = "Mostra tutti i valori attualmente nel db"
#         self.lay_obj.tooltips.set_tip(item,label)
#         menu.append(item)

        ## possible values regexp
        item = gtk.MenuItem(label="possible values: regexp ")
        item.connect('activate', self.show_possible_values, field_name, 'regexp')
        label = "Mostra tutti i valori attualmente nel db che 'matchino'"
        self.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## possible values starting
        item = gtk.MenuItem(label="possible values, starting ")
        item.connect('activate', self.show_possible_values, field_name, 'start')
        label = "Mostra tutti i valori attualmente nel db, che cominciano con..."
        self.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        
        return True

