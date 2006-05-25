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

class SqlWidget(object):
    fields   = None  # fields to use (InspectMapper)
#    tables = None    # Table objects referenced as foreign keys
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
                  order_by=None,
                  show=True,
                  single=False
                  ):
        """create an interface and allow to save/store data from a database

        mapper: a sqlalchemy mapper
        lay:    a layout describing the desired layout (see layout package)
        validator: a validator to be used to validate fields and records
        naked:  in case the mask should *not* be added interactive buttons
                neede if the layout already contains all the required buttons
        mode:   ro|rw. When in read-only no save/delete is alllowed
        noup:   list of field-name that cannot be updated, may be a comma
                separated str
        show:   True|False
        single: this is a single application. connect a gtk.quit()
        """
        
        self.sync_list = []
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
        self.completion = completion.Completion(self)
        ## create the interface and add obvious constraints
        self.naked = naked
        self.lay   = lay
        self.sql   = sql
        self.single = single
        if show:
            self.show()
            
    def show(self):
        """create the widget and go on displaying the layout
        """
        self.lay_obj, self.w  = self._get_layout(self.lay, self.naked)
        if self.sql:
            self.reload(self.sql)
            
        ## only render when dimentions are complete
        self.w['Window'].show()
#         if self.__class__.__name__ == 'SdTable':
#             self.show_myself()
            
        

    def _get_validator(self, valid):
        if not valid:
            valid = validator.Validator()
        self.valid = valid
        
    def _get_layout(self, lay, naked):
        ## layout
        #dbg.write('target', self.Class)
        lay = TableLayoutGenerator(self.fields, naked=naked, lay=lay,
                                   target=self.__class__.__name__).layout

        self.layout = lay
        self.add_filter(visible=False)

        ## add default buttons if needed
        #self._add_default_buttons(naked)
        #dbg.write(self.layout)
        self.lay_obj = layout.Layout(self.layout, title=self.title, opts='T-')
        #self.lay_obj.xml('/tmp/m.glade')
        self.lay_obj.prop('Window', 'visible', False)
        self.w       = self.lay_obj.show()

        if self.__class__.__name__ == 'SqlMask':
            self._analize_widgets_in_layout()
            self._add_constraints_and_connect()
            self._add_colors_and_fonts()
        
        self._add_actions_to_buttons()
        self._fill_menubar_menu()
        return (self.lay_obj, self.w)
    
    def _add_actions_to_buttons(self):
        """ Add default actions to std buttons"""
        actions = {
            ## std toolbutton
            'tb=gtk-save'       : self.record_save,
            'tb=gtk-new'        : self.record_clear,
            'tb=gtk-delete'     : self.record_delete,
            'tb=gtk-refresh'    : self.reload_cb,
            'tb=gtk-quit'       : self.delete_event,
            'tb=gtk-go-forward' : self.record_forward,
            'tb=gtk-go-back'    : self.record_back,

            ## in case the programmers has set them
            'b=gtk-save'       : self.record_save,
            'b=gtk-new'        : self.record_clear,
            'b=gtk-delete'     : self.record_delete,
            'b=gtk-refresh'    : self.reload_cb,
            'b=gtk-quit'       : self.delete_event,
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
    

####### Record browsing & saving
    def record_delete(self, widget=None):
        """invokes the validator before DELETing a record"""
        pass
    
    def record_save(self, ev):
        """invokes the validator before UPDATE/INSERT a record"""
        pass
    def record_save_new(self):
        """Insert a new record
        """
        pass
    
    def record_clear(self, widget=None):
        """clear the mask for a new record"""
        pass
    
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

    def record_forward(self):
        """it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing"""
        pass
    def record_back(self):
        """it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing"""
        pass
    
    def sync_add(self, sqlWidget):
        self.sync_list += [sqlWidget]

    def sync(self):
        """emit a reload to other SqlWidgets so that they keep in sync"""
        for w in self.sync_list:
            sql = []
            val = {}
            for field_name in w.get_pk():
                sql += ["%s = :%s" % (field_name,field_name)]
                val[field_name] = self._get_value(field_name)
                dbg.write(sql)
            w.reload(  sql =  (and_(*sql),val)   )

    def get_pk(self):
        """return the pkeys of the primarytable"""
        return self.fields.pkeys[self.fields.get_primary_table()]

####### Validation
    def digits_check_input_cb(self, widget, event):
        """prevents the possibility of inputting wrong chars"""
        ## fixme: missing comma, and cut&paste
        key = gtk.gdk.keyval_name (event.keyval)
        #dbg.write(key)
        ONLYDIGITS="([0-9.,]|BackSpace|Left|Right|F1|period|Tab|Up|Down)"
        if not re.match (ONLYDIGITS, key):
            #dbg.write("key: %s" % key)
            return True
        

####### Misc
    def delete_event(self, widget):
        """Quit operations: check if need to save first """
        ### fixme: must add cheks
        ### fixme2: must the toplevel be destrouyed (or is reparented?)
        #print widget
        self.w['Window'].destroy()
        self.filter_panel.destroy()
        if self.single:
            self.gquit()
        
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
        
    def show_widget_info(self, *args):
        dbg.gtk_dbg.show_widgets()
        
    def show_class_info(self, *args):
        dbg.gtk_dbg.ShowClassInfo(self) 
        
    def show_widgets(self, *args):
        import dbg.gtk_dbg
        dbg.gtk_dbg.show_widgets(self.w['Window'])
    
    def _fill_menubar_menu(self):
        """here all menus are filled for filtering,  sorting, ro, query..."""
        if 'm=file' in self.w:
            self.lay_obj.menu('m=file',
                              ('filter panel', self.add_filter),
                              ('-', None),
                              ('inspect tables', self.show_mapper_info),
                              ('inspect widgets', self.show_widget_info),
                              ('inspect class', self.show_class_info),
                              ('-', None),
                              ('gtk-quit', self.delete_event)
                              )
    

