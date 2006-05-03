import sys, re, datetime
import config
import inspect
import layout
import layout.dateedit as dateedit

import validator
from layoutgenerator import TableLayoutGenerator
import gtk, pango
from sqlalchemy import *
import sqlfilter, dbg
import sqldata

class LookupValueNotReturningOneValue(Exception): pass
class MissingDescriptorField(Exception): pass
class FieldNotInLayout(Exception): pass

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
                  mode='rw',
                  noup=None,
                  sql=None,
                  constraint=None,
                  engine=None,
                  title=None
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
        self.mapper = self._get_mapper(mapper, table)
        if not engine:
            self.engine = self.mapper.table.engine
        self.valid = self._get_validator(valid)
        self.listores = {}  ## needed for entry_completion
        self.fields = inspect.InspectMapper(self.mapper, noup=noup, mode=mode)
        self.title = self._get_title(title)
        self.tables = {}
        self.values = {}

        ## create the interface and add obvious constraints
        self.lay_obj, self.w  = self._get_layout(lay, naked)
        ## fill in the data in case
#         if records:
#             dbg.debug('ora self.record_display, records: ' % records)
#             self.record_display()
        if sql:
            #dbg.debug('__init__ sql: %s' % sql)
            self.reload(sql)
            
        ## only render when dimentions are complete
        self.w['Window'].show()

####### Record browsing & saving
    def record_display(self, record=None, incr=0):
        """display a mapped record in the mask

        display the data provided by self.sqlData.get()
        incr: incr=incr arg to sqlData.get()
        """
        #dbg.debug('Record_display n: %s' % self.sqlData.index())
        ## fill in the data

        data_in = self.sqlData.get(incr=incr)
        #dbg.debug("data_in", data_in)
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
        #dbg.debug("%s: %s" % (field_name, field_value))
        # [0]: the gtkClass
        # [1]: the gtkWidget
        if field_name not in self.mwidgets:
            return
        widget = self.mwidgets[field_name][1]

        if self.fields[field_name]['fkey'] and field_name.endswith('_id'):
            self.values[field_name] = field_value
            field_value = self._lookup_value(field_name, field_value)
            

        #dbg.debug( "name: %s type: %s" % ( field_name, self.fields[field_name] ))
        # Entry
        if isinstance (widget, gtk.Entry):
            if field_value == None:
                field_value = ''
            widget.set_text( str(field_value) )
        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            if field_value == '':
                return
            widget.set_property('time', field_value)

        # Boolean
        elif self.fields[field_name]['type'] == bool:
            if not field_value :
#                 dbg.debug("impongo false per %s che era '%s'" % (
#                     field_name, field_value))
                field_value = False
            widget.set_active(field_value)
            #dbg.debug("%s: %s" % (field_value, widget.get_active()))
        
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
        #dbg.debug(objectstore.commit())
        objectstore.commit()
        #dbg.debug(self.record_clear())
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
            #dbg.debug(field_name, value)
            
            t = self.fields[field_name]['type']
            #dbg.debug("%s: - value: %r T: %s" % (field_name, value, t))
            if t == datetime.date:
                value = t(value.year, value.month, value.day)
            elif t == datetime.datetime:
                value = t(value.year, value.month, value.day,
                          value.hour, value.minute, value.second)
                continue
            else:
                if value is not None:
                    #dbg.debug("value is", value)
                    value = t(value)

            if value != self.data_in[field_name]:
                #dbg.debug("%s: %r is not %r" % (field_name,
                #                               value, self.data_in[field_name]))
                R[field_name] = value

        #dbg.debug(R)
        self.sqlData.set(R)

        objectstore.commit ()
        
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
            #dbg.debug("%s: - value: %r t: %s" % (field_name, value, t))
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

        #dbg.debug(R)
        self.sqlData.add(R)
        self.status = self.sqlData.get_current()
        dbg.debug("self.status", self.status)

        objectstore.commit ()
        self.record_display()
        
    def record_clear(self, widget=None):
        """clear the mask for a new record"""
        #dbg.debug('')
        self.values.clear()
        self.status = None
        
        for field_name in self.fields.keys():
            #dbg.debug(field_name)
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
        #dbg.debug(sql)
        if isinstance(sql, tuple) and len(sql) == 2:
            sql_str, params = sql
            #dbg.sql_debug(sql_str, params)
        else:
            sql_str = sql
            params = None
            
        records = self.mapper.select(sql_str, params=params, limit=limit)
        self.sqlData = sqldata.SqlData(records, mapper_info=self.fields)
        self.record_display()
    
    def reload_cb(self, widget):
        """issue a reload operation on master. Call back of reload button"""
        #limit=100
        self.reload( )

    
    def _lookup_value(self, field_name, field_value):
        """retrieve the value in a lookup table in case of foreign_key
        """
        if not field_value:
            return ''
        #dbg.debug("%s %s" % (field_name,field_value))
        ftable, fname = self.fields[field_name]['fkey']
        sql = "SELECT %s FROM %s WHERE %s = :%s" % (
            self._add_descriptor_fields(mode='return', table_name=ftable),
            ftable, field_name, fname)
        t = text(sql, engine=self.engine)
        ret = t.execute(**{field_name : field_value})
        j = 0
        for R in ret:
            value = R[0]
            j += 1
        if not j == 1:
            raise LookupValueNotReturningOneValue("%s returns %s values" % (sql, j))
        return value
                                               
####### Layout, Reflection & Analisys
    def _get_mapper(self, mapper_obj, table):
        """If no mapper is provided it will be built from the table"""
        ## FIXME: manca parte creazione mapper
        if mapper_obj:
            return mapper_obj
        elif table:
            #class abc(object): pass
            name = "%s_class" % (table)
            sa_table = Table(table, engine=self.engine, autoload=True)
            X = type(name, (object,), {})
            return mapper(X, sa_table)
    
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
        #dbg.debug(self.layout)
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
            #dbg.debug("_analize_widget_layout: %s" % (field_name))
            for mod in ('e','d','r','m','c'):
                try:
                    widget = self.w["%s=%s" % (mod, field_name)]
                    self.mwidgets[field_name] = (type(widget), widget)
                except:
                    pass
            # (gtkClass , gtkWidget)

        ## all EventBox 
        #dbg.debug("self.w: %s" % self.w)
        #dbg.dshow(self.w, 'E=')
        self.labels = {}
        #dbg.debug(self.fields.keys())
        for field_name in self.fields.keys():
            lbl_name_wdg = "l=%s" % field_name
            if lbl_name_wdg in self.w:
                self.labels[field_name] = self.w[lbl_name_wdg]
                #dbg.debug("%s -> %s"% (field_name, self.labels[field_name]))
            else:
                #dbg.debug("Missing event_box for %s" % (field_name))
                pass
            
    def _fill_menubar_menu(self):
        """here all menus are filled for filtering,  sorting, ro, query..."""
        if 'm=file' in self.w:
            self.lay_obj.menu('m=file',
                              ('filter panel', self.add_filter),
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
                    #dbg.debug(field_name)
                    self.labels[field_name].modify_fg(gtk.STATE_NORMAL, FK_COLOR)
            
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
                #dbg.debug("skip %s" % field_name)
                continue
            widget = self.mwidgets[field_name][1]
            if not widget:
                #dbg.debug("Per campo: %s manca widget %s" % (field_name, widget))
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
                #dbg.debug("aggiungo <3> per %s" % (field_name))
                widget.connect('button-press-event',self.pop_menu, field_name, 3)
                widget.connect('key-press-event',self.entry_short_cut_event,
                               field_name, 'F1')
#             else:
#                 dbg.debug("fkey per %s: %s" %
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
            #dbg.debug("<1> x filter: %s %s" % (field_name, event_box))
            event_box = label.parent
            event_box.connect('button-press-event',
                              self.filter_panel.add, field_name, 1)

        # key accelerators
        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_group(ord('h'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.show_widgets)
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
        #dbg.debug(key)
        ONLYDIGITS="([0-9.,]|BackSpace|Left|Right|F1|period|Tab|Up|Down)"
        if not re.match (ONLYDIGITS, key):
            dbg.debug("key: %s" % key)
            return True
    
####### Misc
    def quit(self, widget):
        """Quit operations: check if need to save first """
        ### fixme: must add cheks
        ### fixme2: must the toplevel be destrouyed (or is reparented?)
        #print widget
        self.w['Window'].destroy()
        self.filter_panel.destroy()
        
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
            
    
    def show_widgets(self, *args):
        import dbg.gtk_dbg
        dbg.gtk_dbg.show_widgets(self.w['Window'])
    
####### Completion
# EntryCompletion widgets are added on the fly triggered by F1, C-F1 or menu items
# select_values will get data from the db and fill a listore
# match_function filters using re.search from the listore to fill in the completion
#
    def add_completion(self, field_name, mode):
        """ add a completionEntry to an Entry
        return a listore to be filled

        ForeignKey: when the field to comlete is a foreign key, the lookup table
        is analized to search if a descriptor field exits. In that case a
        cellRenderer is added to the completion to choe that data and that field is
        used in the field
        """

        entry = self.mwidgets[field_name][1]
        completion = entry.get_completion()
        if completion:
            return (completion.get_model(), completion)

        ## completion was not present
        completion = gtk.EntryCompletion()
        completion.set_property('minimum-key-length', 0)
        completion.connect('match-selected', self.match_selected_cb, field_name)
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)
            
        ## FIXME: piu' generale per caso in cui si mettano anche altri campi
        if self.fields[field_name]['fkey']:
            col_num = 2
        else:
            col_num = 1
            
        listore = gtk.ListStore(*[str for x in range(col_num)])
            
        ## we match against the description field
        completion.set_match_func(self.match_func, (col_num-1, mode))

        self.listores[field_name] =  listore
        if mode == 'regexp':
            completion.insert_action_text(1,'start with...')
        else:
            completion.insert_action_text(2,'regexp')

        completion.set_model(listore)
        completion.set_inline_completion(True)
        entry.set_completion(completion)
        completion.set_text_column(col_num-1)
        return (listore, completion)
    def match_selected_cb(self, wdg, model, iter, field_name):
        """after selecting an entry store the value in self.values
        """
        self.values[field_name] = model.get(iter,0)[0]
        
    def match_func(self, completion, key, iter, func_data):
        column, mode = func_data
        model = completion.get_model()
        text = model.get_value(iter, column)
        #dbg.debug("column: %s  - mode: %s" % (column, mode))
        if not text:
            text = ''
        #return False
        # start
        if mode == 'start':
            if re.search("^%s" %(key), text, re.IGNORECASE):
                return True
            else:
                return False
        # regexp
        if re.search(key, text, re.IGNORECASE):
            #dbg.debug("accetto: %s col: %s" % (text, column))
            return True
        #dbg.debug("rifiuto: %s" % text)
        return False
    def show_field_info(self, wdg, field_name):
        """Pop a dialog to give info on the selected field"""
#         dialog = gtk.Dialog("info on %s" % field_name,
#                             None, gtk.DIALOG_MODAL,
#                             (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT) )
        info = ["%s: %s" % (f, self.fields[field_name][f]) 
                           for f in self.fields[field_name].keys() ]
#        label = gtk.Label("\n".join(info) )

        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, type=gtk.MESSAGE_INFO,
                                   buttons=gtk.BUTTONS_OK,
                                   message_format="\n".join(info))
        #dialog.action_area.pack_start(label, gtk.TRUE, gtk.TRUE, 0)
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            dialog.destroy()
    
    def entry_short_cut_event(self, wdg, ev, field_name, key):
        """callback of key-press-button in (string) entries"""

        accelname = gtk.accelerator_name(ev.keyval, ev.state)
        if accelname == 'F1':
            self.show_possible_values (wdg, field_name, 'regexp')
        elif accelname == '<Control>F1':
            self.show_possible_values (wdg, field_name, 'start')
    
    def show_possible_values(self, wdg, field_name, mode):
        """fill in a ListStore to use with completion, fetch data from db
        mode determines the match of the already typed text:
        start: only matching data starting with typed text
        regexp: typed text is a regexp (*~ or ILIKE)
        all: all values
        """
        #print "show_possible_values %s" % field_name
        sql_dict = {}
        sql_dict['val'] = self.mwidgets[field_name][1].get_text()
        if mode == 'start':
            sql_dict['oper'] = 'ILIKE'
            val = '%'
        if mode == 'regexp':
            sql_dict['oper'] = '~*'
        else:
            sql_dict['oper'] = '~'
            sql_dict['val'] = "."

        sql_dict['field_name'] = field_name
            
        listore, completion = self.add_completion(field_name, mode)
        listore.clear()
        ret = self.select_values(field_name, sql_dict)
        ## sql_dict['field_name'] may be changed by select_values if fk
        #dbg.debug("field_name %s" % (sql_dict['field_name']))
        #dbg.debug("listore is: %s" % listore)
        for R in ret:
            #listore.append([getattr(R, sql_dict['field_name'])])
            dbg.debug("R: %s" % R)
            listore.append(R)
#        completion.complete()
        event =   gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        event.keyval = gtk.keysyms.period  #ord(".")
        event.window = self.mwidgets[field_name][1].window
        self.mwidgets[field_name][1].emit('key-press-event',event)
        event.keyval = gtk.keysyms.BackSpace
        event.hardware_keycode = 22
        #event.window = self.mwidgets[field_name][1].window
        ## FIXME: non funziona
        self.mwidgets[field_name][1].emit('key-press-event',event)
        
    def select_values(self, field_name, sql_dict):
        """execute the SELECT DISTINCT and return values
        In case FKeys it behaves in a much more complicated way.
        The aim is to substitute the referenced value with the value that will
        normally be an id. It will try to do that *if* the name of the field
        terminates with _id.

        """

        I = self.fields[field_name]
        exec_dict={field_name : sql_dict['val']}
        ### field is a ForeignKey
        if I['fkey']:
            sql_dict['table_name'] = I['fkey'][0]
            sql_dict['field_name'] = I['fkey'][1]
            self._add_descriptor_fields(sql_dict)
            sql = """SELECT DISTINCT %(field_name)s,%(descr)s
                 FROM %(table_name)s 
                 WHERE %(descr)s %(oper)s :%(descr)s
                 ORDER BY %(descr)s
                 """ % sql_dict
            exec_dict.update({sql_dict['descr'] : sql_dict['val']})
        else:
            sql_dict['table_name'] = I['table_name']

            if I['type'] == int:
                ## pointless to regexp numbers...
                sql = """SELECT DISTINCT %(field_name)s
                FROM %(table_name)s 
                ORDER BY %(field_name)s
                """ % sql_dict
            else:
                sql = """SELECT DISTINCT %(field_name)s
                    FROM %(table_name)s 
                    WHERE %(field_name)s %(oper)s :%(field_name)s
                    ORDER BY %(field_name)s
                    """ % sql_dict

        dbg.sql_debug(sql, exec_dict)
#        s = text(sql, engine=self.mapper.engines[0])
        s = text(sql, engine=self.mapper.table.engine)
        return s.execute(**exec_dict)
    def pop_menu(self, wdg, ev, field_name, num_button):
        #print "pop_menu", wdg, ev
        if not ev.button == num_button:
            return False

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
        item = gtk.MenuItem(label="possible values: regexp  - F1")
        item.connect('activate', self.show_possible_values, field_name, 'regexp')
        label = "Mostra tutti i valori attualmente nel db che 'matchino'"
        self.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## possible values starting
        item = gtk.MenuItem(label="possible values, starting - Ctrl-F1")
        item.connect('activate', self.show_possible_values, field_name, 'start')
        label = "Mostra tutti i valori attualmente nel db, che cominciano con..."
        self.lay_obj.tooltips.set_tip(item,label)
        menu.append(item)

        ## edit table referenced as foreign key
        item = gtk.MenuItem(label="Edit fk table")
        item.connect('activate', self.edit_foreign_key_table, field_name)
        label = "Edita la tabella da cui sono presi i valori permessi per questo \
        campo"
        self.lay_obj.tooltips.set_tip(item, label)
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        
        return True
    def _add_descriptor_fields(self, sql_dict=None, mode='add', table_name=None):
        """search a possible field descriptor and add it to sql_dict

        When displaying data for foreign keys the key that is referenced may be
        a serial or a code. A descriptor field can be shown instead. A default is
        to look for the first field terminating with _name or _descr.

        You can bypass this mechanism writing a comma separated list in
        SqlMask.tables[table_name] = [field_name[,field_name], [format]]

        In the future 'format' will hold format info for the completion entry

        """
        
        if not table_name:
            table_name = sql_dict['table_name']
            
        if table_name not in self.tables:
            table = Table(table_name, engine=self.engine, autoload=True)
            #dbg.debug("type: %s" % type(table))              
            #dbg.debug("ora: table %s - keys: %s" % (table, table.c.keys()))
            
            #self.tables[table_name] = table
            for field_name in table.c.keys():
                #dbg.debug("cercao %s" % field_name)
                if re.search('_name|_descr', field_name, re.I):
                    self.tables[table_name] = list([field_name])
                    #dbg.debug(self.tables[table_name])
                    break
#                 else:
#                     dbg.debug("%s non finisce per _name|_descr" % field_name)
            
        if table_name in self.tables:
            if mode == 'add':
                #sql_dict['field_name'] += ",%s" % self.tables[table_name][0]
                sql_dict['descr'] = self.tables[table_name][0]
            else:
                return self.tables[table_name][0]
        else:
            txt = "table %s does not have a descriptor field \
            to use instead of id: %s" % (table_name, table.c.keys())
            raise MissingDescriptorField(txt)
    
    def edit_foreign_key_table(self, wdg, field):
        """opens a SqlMask to edit the table referenced by this ForeignKey"""

        tbl  = self.fields[field]['table_name']
        fkey = self.fields[field]['fkey']
        txt = "table:  %s - fkey: %s" % (tbl, fkey)
        dbg.debug(txt)
    

