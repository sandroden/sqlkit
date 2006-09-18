import sys, re, datetime, os
#import config
import inspect 
#import common
import layout
import layout.dateedit as dateedit

from layoutgenerator import TableLayoutGenerator
import gtk, pango
import decimal
from sqlalchemy import *
import dbg.gtk_dbg

import sqlkit
import sqlkit.sqlfilter as sqlfilter
import sqlkit.sqldata as sqldata
import sqlkit.minspect as minspect
import sqlkit.parseopts as parseopts
import sqlkit.completion as completion
#from misc import rebuild
#import new
#import misc.autoreload

class NoSyncError(Exception): pass
class SyncNotAvailable(Exception): pass
class MissingEngine(Exception): pass
NUMBERS = (int, float, decimal.Decimal)

class SqlWidget(object):
    fields   = None  # fields to use (InspectMapper)
#    tables = None    # Table objects referenced as foreign keys
    values = None    # real value for foreign key (when lookup is displeyed instead)
#    __metaclass__ = dbg.LogTheMethods
#    __metaclass__ = misc.autoreload.MetaAutoReloader
    
    def __init__ (self, mapper=None,
                  lay = None,
                  naked=False,
                  table=None,
                  tables=None,
                  join=None,
                  mode='rw',
                  noup=[],
                  sql=None,
                  constraint={},
                  engine=None,
                  title=None,
                  order_by=None,
                  show=True,
                  single=False,
                  limit=100,
                  nick=None,
                  geom=(-1,300),
                  addto=None,
                  actions=None,
                  field_list=None,
                  session=None,
                  dev=False,
                  xml=False,
                  filter=True,
                  icons='',
                  ):
        """create an interface and allow to save/store data from a database

        mapper: a sqlalchemy mapper
        lay:    a layout describing the desired layout (see layout package)
        actions: a validator to be used to validate fields and records
        naked:  in case the mask should *not* be added interactive buttons
                neede if the layout already contains all the required buttons
        mode:   ro|rw. When in read-only no save/delete is alllowed
        noup:   list of field-name that cannot be updated, may be a comma
                separated str
        show:   True|False
        single: this is a single application. connect a gtk.quit()
        nick is just for debug purpouse
        addto:  passed to layout
        dev:    if dev=False (default) fields ending with '_id' and not fk
                are not shown
        """
        self.block = False
        self.icons = icons
        self.filter = filter
        self.nick= nick
        self.xml = xml
        self.dev = dev
        # used in self.reload() to prevent expose loop 
        self.reloading = dbg.TraceIt(False, name='reloading')
        self.geom = geom
        self.addto = addto
        self.actions = self.get_actions(actions)
        self.constraint=constraint
        self.sync_dict = {}
        self.engine = self.get_engine(engine, mapper)
        self.session = self.get_session(session)
        self.order_by = order_by
        ## we can use singular or plural as an option, plural in the code
        if table and not tables:
            tables = table
        self.tables = tables
        self.mapper = self.get_mapper(self.engine, mapper, tables)
        self.mode = mode
        self.fields = parseopts.inspect_mapper(self.mapper, noup=noup, mode=mode)
        self.field_list = self.parse_fields(field_list)
        self.title = self._get_title(title)
#        self.tables = {}
        self.values = {}
        self.completion = completion.Completion(self)
        ## create the interface and add obvious constraints
        self.naked = naked
        self.lay   = lay
        self.sql   = sql
        self.sqlData = sqldata.SqlData(None, self.fields, self.session)
        self.single = single
        self.limit=limit
        if show:
            self.show()
            
    def show(self):
        """create the widget and go on displaying the layout
        """
        self.lay_obj, self.w  = self._get_layout(self.lay, self.naked)
#         if self.sql or isinstance(self, sqlkit.table.SqlTable):
#             self.reload(self.sql, limit=self.limit)
            
        ## only render when dimentions are complete
        #self.w['Window'].show()
        lcontainer_name = self.lay_obj.container().el_def
        el_def = re.sub(':.*','', lcontainer_name)
        #dbg.write('lcontainer_name: ', el_def)
        self.w[el_def].show()
        
    def get_session(self, session):
        if session:
            return session
        else:
            return create_session()
    
    def get_mapper(self, engine, mapper, tables):
        return parseopts.get_mapper(self.engine, mapper, tables)
        
    def parse_fields(self, fields):
        if not fields:
            if self.dev:
                fields = self.fields.keys()
            else:
                ## I want all fields not ending with _id
                ## *AND* all fields that REFERENCE other keys
                ## i.e.: if you have city_id that references a city I want
                ## to see it, but I don't want to see a sequence normally.
                fields = [f for f in self.fields.keys()
                          if not f.endswith('_id') or self.fields[f]['fkey'] ]

            
        if isinstance(fields, str):
            fields = re.split('[ ,]+',fields)
        #dbg.write(self.nick, fields)
        return fields
    
    def get_actions(self, actions):
        if not actions:
            actions = Actions()
        actions.master = self
        return actions
    
    def get_engine(self, engine, mapper):
        if not engine:
            if mapper:
                dbg.write(mapper)
                engine = mapper.local_table.engine
            else:
                try:
                    engine = schema.default_metadata.engine
                except:
                    msg = "You may want to use globalconn when creating engine"
                    raise MissingEngine(msg)
                
        return engine
    
    def _get_layout(self, lay, naked):
        ## layout
        #dbg.write('target', self.Class)

        if isinstance(lay, sqlkit.SqlMask):
            #dbg.write()
            self.w = lay.w
            self.filter_panel = lay.filter_panel
            ## NOTE: here I say that I can reach w/ _get_value also the
            ##       values of the secondary mask. Of course you need to be
            ##       carefull not to mix up filed-names
            self.mwidgets = lay.mwidgets
            self._analize_widgets_in_layout()
            self._add_constraints_and_connect()
            self._add_colors_and_fonts()
            self.values = lay.values
            return (lay.lay_obj, lay.w)
        
        lay = TableLayoutGenerator(self, naked=naked, lay=lay).layout
        self.layout = lay
        #dbg.write(self.layout)
        self.add_filter(visible=False)

        ## add default buttons if needed
        #self._add_default_buttons(naked)
        #print self.layout
        #dbg.write(self.layout)
        self.lay_obj = layout.Layout(self.layout, addto=self.addto,
                                     title=self.title, opts='T-')
        if self.xml:
            self.lay_obj.xml('/tmp/m_%s.glade' % self.nick)
        if 'Window' in self.lay_obj.elements:
            self.lay_obj.prop('Window', 'visible', False)
        self.w       = self.lay_obj.show()

        if 'Window' in self.lay_obj.elements:
            self.lay_obj.connect(('Window', 'delete_event', self.delete_event))


        if isinstance(self, sqlkit.SqlMask):
            self._analize_widgets_in_layout()
            self._add_constraints_and_connect()
            self._add_colors_and_fonts()


        self._add_actions_to_buttons()
        self._fill_menubar_menu()
        self.add_accelerators()
        return (self.lay_obj, self.w)
    
    def add_accelerators(self):
        # key accelerators
        if self.addto:
            return
        
        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_group(ord('h'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.show_widgets)
        self.accel_group.connect_group(ord('q'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.gquit)
#         self.accel_group.connect_group(ord('n'), 
#                                        gtk.gdk.CONTROL_MASK, 
#                                        gtk.ACCEL_LOCKED, 
#                                        self.record_clear)
#         self.accel_group.connect_group(ord('s'), 
#                                        gtk.gdk.CONTROL_MASK, 
#                                        gtk.ACCEL_LOCKED, 
#                                        self.record_save)
        self.w['Window'].add_accel_group(self.accel_group)
            
        
    def _add_actions_to_buttons(self):
        """ Add default actions to std buttons"""
        actions = {
            ## std toolbutton
            'tb=gtk-save'       : self.record_save,
            'tb=gtk-new'        : self.record_new,
            'tb=gtk-delete'     : self.record_delete,
            'tb=gtk-refresh'    : self.reload_cb,
            'tb=gtk-quit'       : self.delete_event,
            'tb=gtk-go-forward' : self.record_forward,
            'tb=gtk-go-back'    : self.record_back,

            ## in case the programmers has set them
            'b=gtk-save'       : self.record_save,
            'b=gtk-new'        : self.record_new,
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
                #self.w[widget_name].connect('clicked', handler)
                self.lay_obj.connect((widget_name, 'clicked', handler))
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
    def record_save_new(self, wdg, constraint):
        """Insert a new record
        """
        pass
    
    def clear(self, widget=None):
        """clear the mask for a new record"""
        pass
    
    def reload(self, sql=None, params=None, limit=100, constraint={},
               reload_constraint=False, display=True):
        """reload data from db

        sql may be a tuple (sql_statement, bind_params) or just a sql_statement
        """

        if constraint:
            self.constraint=constraint
        #dbg.write(self.nick, 'constraint', constraint)

        if sql is None:
            sql = self.sql

        if isinstance(sql, tuple) and len(sql) == 2:
            sql_str, params = sql
            #dbg.write('type sql_str', type(sql_str), 'type params', type(params))
            #dbg.sql_debug(sql_str, params)
        else:
            sql_str = sql
            params = None

        if reload_constraint == True:
            #dbg.write("add self.reload_sql_constraint", sql_str)
            self.sql = (sql_str, params)

        self.session.clear()
        #dbg.write(self.nick, "SQL: '%s'" % sql_str,
        #           'params', params, 'limit:', limit)
        #self.mapper.table.engine.echo = True
        records = self.session.query(self.mapper).select(sql_str, params=params,
                                                         order_by=self.order_by,
                                                         limit=limit)
        if self.nick == 'art_var_filo':
            self.engine.echo = False
        #records = self.mapper.select_by(sql)
        #self.mapper.table.engine.echo = False
        if isinstance(self, sqlkit.SqlMask):
            self.clear()
        self.sqlData = sqldata.SqlData(records, self.fields, self.session)
        if display:
            self.record_display()

        return self.sqlData.count()

    def reload_one(self,field, value):
        """compact way to view a single record or records with a single property"""

        sql = "%s = :%s" % (field, field)
        bind_parameters = {field : value}
        
        self.reload(  (sql, bind_parameters)  )

    def reload_cb(self, widget):
        """issue a reload operation on master. Call back of reload button"""
        #limit=100
        self.reload( )
    def commit(self):
        PREV = self.engine.echo
        if dbg.debug() > 1:
            #dbg.write('dbg.debug()', dbg.debug())
            pass
            self.engine.echo = True
            
        try:
            self.session.flush()
        except exceptions.SQLError, e:
            print e
            self.SQLErrorHandler(e)

        self.engine.echo = PREV
    
    def SQLErrorHandler(self, e):
        self.sb(e.orig)
        dbg.write("Scritto %s su sb" % (e.orig))
            
    def record_forward(self):
        """it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing"""
        pass
    def record_back(self):
        """it doesn't make any sense here, but we need it to prevent
        _add_actions_to_button from failing"""
        pass
    
    def sync_add(self, sqlWidget, cnd=None):
        if not isinstance(self, sqlkit.SqlMask):
            raise SyncNotAvailable("Sync only available for SqlMask")

        # sqlWidget : (DIR, cnd_str, field_names )
        if not cnd:
            DIR, cnd_str, fields_dict = minspect.get_join_cnd_for_sync(
                self.mapper.local_table, sqlWidget.mapper.local_table)
        else:
            DIR, cnd_str, fields_dict = cnd
            
        self.sync_dict[sqlWidget] = (DIR, cnd_str, fields_dict )
        ## a synced widget should not be edited if we don't have a record to sync...
        if len(self.sqlData) == 0:
            sqlWidget.sync_block()

        dbg.write(DIR, direct=False)
#        sqlWidget.reload_constraint(cnd_str)
#         if sqlWidget.get_pk() != field_names:
#             raise NoSyncError("non campi suff per match %s != %s" % (sqlWidget.get_pk(), field_names))
    def sync(self):
        """emit a reload to other SqlWidgets so that they keep in sync"""
        ## easy/simple (almost useless) case: we have a Many2One relation. A field
        ## of primarytable has a fk to another table
        #dbg.write(self.nick)
        for w, value in self.sync_dict.iteritems():
            #dbg.write(w, value)
            #DIR, sql, field_names, fkeys = value
            DIR, sql, fields_dict = value
            val = {}
            val_constr = {}

            ## constraints
            for name, referenced_name in fields_dict.iteritems():
                #name, referenced_name = fkey
                #dbg.write(name, self._get_value(referenced_name, data=True))
                val_constr[referenced_name] = self._get_value(name, data=True)

            ## bind_params
            for field_name in fields_dict.keys():
                val[field_name] = self._get_value(field_name, data=True)

            #dbg.write(sql, val)
#            w.reload(  sql =  (and_(*[sql]),val)   )
            w.clear()
            w.reload(  sql =  (sql,val) , constraint=val_constr,
                       reload_constraint=True  )
            w.sync_unblock()
            
    def get_pk(self):
        """return the pkeys of the primarytable"""
        return self.fields.pkeys[self.fields.get_primary_table()]
    
    def sync_block(self):
        """When a master is syncing this widget, we must block interaction until
        the master has inserted an id and set a constraint"""
        self.block = True
    
    def sync_unblock(self):
        """When a master is syncing this widget, we must block interaction until
        the master has inserted an id and set a constraint"""
        self.block = False
    

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
    def record_display(self, record=None, incr=0):
        self.actions.on_record_display()
        

####### Dialog
    def dialog(self, type='yes-no', text='', title=''):
        dialog, l = self.lay_obj.dialog(lay="l=a", title=title,
                                        type=type, show=False)
        l.prop(('l=a', 'use_markup', True))
        l.widgets['l=a'].set_markup(
            '<span size="14000">%s</span>' % text)
        dialog.show_all()
        return dialog
    
    def message(self, type='question', text='', title=''):
        self.response = None
        dialog, l = self.lay_obj.message(title=title, text=text,
                                        type=type, show=False)
        dialog.connect('response', self.response_cb )
#        dialog.show_all()
        dialog.run()
        return dialog
    
    def response_cb(self, dialog, butt_id):
        self.response = butt_id

####### Misc
    def set_fkey_value(self, field_name, value):
        """needed for completion, to set real value when
        description is shown instead
        """
        pass
    def delete_event(self, *args):
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
                title= self.fields.get_primary_table()
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
                              ('filter panel',  'activate', self.add_filter),
                              ('-', None),
                              ('inspect tables', 'activate',  self.show_mapper_info),
                              ('inspect widgets', 'activate', self.show_widget_info),
                              ('inspect class', 'activate', self.show_class_info),
                              ('-', None),
                              ('gtk-quit', 'activate', self.delete_event)
                              )
            self.printing()

####### printing
    def printing(self):
        """this will pop entries in the print setup to allow for printing
        A mask will be printed only if a template (.sxw) is provided
        in one of these two ways:
        1. directly set self.print_template pointing to a .sxw file
        2. directly set self.print_template_dir pointing to a directory where
                    many possible templates are.
        3. setting a global dir sqlkit.set_template_dir(). In this case a
                    template will be searched for in a subdir named self.nick

        When a tempate is found the name of the template is stripped of the
        trailing suffix .sxw and that name is used as entry for the menu
        """
        
        Menu = self.w['M=file']
        Item = gtk.ImageMenuItem('gtk-print')
        Menu.insert(Item, 2)
        SubMenu = gtk.Menu()
        Item.set_submenu(SubMenu)

        Item.connect('activate', self.print_fill_submenu, SubMenu)
        Menu.show_all()

        #Item1 = gtk.MenuItem('template 1')
        #SubMenu.append(Item1)
    
    def print_fill_submenu(self, item, sub):
        try:
            a = self.printing_menu_filled
            return
        except:
            pass
        
        # check if a printing sistem is there
        templates, template_dir = self.get_templates()

        for template in templates:
            for format in template[1]:
                item = gtk.MenuItem("%s - %s" % (template[0], format))
                item.connect('activate', self.print_file, template[2], format)
                sub.append(item)

        if not templates:
            item = gtk.MenuItem("No templates for nick '%s' in %s" %
                                (self.nick, template_dir) )
            sub.append(item)
            
        sub.show_all()
        self.printing_menu_filled = True
                
    def get_templates(self):
        "return a list of tuples (name.sxw, entry name) for each template found"

        filenames = []
        try:
            template = self.print_template
            self.template2tuple(template, filenames)
        except:
            pass

        template_dir = ""
        try:
            template_dir = self.print_template_dir
        except:
            try:
                template_dir = print_template_dir
            except:
                pass

        if template_dir:

            ## look for a subdir self.nick, this may fail becouse you didn't
            ## define the nick or becouse there is no foulder

            for d in os.listdir(template_dir):
                if d == self.nick:
                    path = os.path.join(template_dir, d)
                    if os.path.isdir(path):
                        ## here are the templates for us
                        for f in os.listdir(path):
                            self.parse_template_and_add(f, filenames, path)

        return (filenames, template_dir)
    
    def parse_template_and_add(self, template, filenames, path=None):                     
        """it check if it is a file, it not just returns. Otherwise it check the
        name to see:
        1. if it ends with .sxw (otherway it returns)
        2. which is the name to use in t menu_entry
        3. if it has sxw or pdf in the name, thus suggesting which transformation
           are allowed. Defaults to just pdf.

           eg: test.sxw  (just pdf output, menu entry 'test')
               my_test_pdf_sxw.sxw  (both output allowed, menu entry: 'my test')
                          note that _ was transformed in space.

        an attempt to further translate the resulting entry is made against
        layout.set_description_fields

        """
        if path:
            template = os.path.join(path, template)

        if not os.path.isfile(template):
            return
        
        formats = []
        base = os.path.basename(template)
        p = re.compile(r"""
            ^(?P<name>.+?)                   # the real name, non greedy fashion
            (_(?P<format>(_?pdf|_?sxw)*))?   # output format encoded
            \.sxw$                           # the extension
        """, re.VERBOSE)
        m = p.match(base)
        if m:
            name = m.group('name')
            name = layout.get_label(name)
            name = name.replace('_', ' ')
            try:
                formats = m.group('format').split('_')
            except:
                formats = m.group('format')
            if formats is None:
                formats = ['pdf']

            filenames.append((name, formats, template))
            
    def print_file(self, item, template, format):

        from ooffice import opop
        import subprocess
        
        page = opop.Sxw(file=template)
        #page.verbose = True
        ret = self.actions.on_print(page)
        if ret is not True :
            self.message(type='warn', text="Missing data")
            return

        outfile = page.make(format=format)
        if isinstance(outfile, list):
            outfile = outfile[0]
        if sys.platform.startswith('linux'):
            if format.startswith('pdf'):
                try:
                    subprocess('acroread %s' % outfile)
                except:
                    try:
                        os.system('gv %s' % outfile)
                    except:
                        try:
                            os.system('xpdf %s' % outfile)
                        except:
                            pass
                        
            elif format == 'sxw':
                os.system('ooffice %s' % outfile)
            
        else:
            os.startfile(outfile)
        page.clean()

####### More
class Actions(object):
    def __init__(self, master=None):
        self.master = master
    
    def on_update(self, new, old):
        pass
    
    def on_delete(self, new, old):
        pass
    
    def on_insert(self, new):
        """invoked after any constraint is applied"""
        pass
    
    def on_record_display(self, new=None):
        """only defined for SqlMask"""
        pass
    
    def on_print(self, page):
        """should prepare all variables needed by pyopenoffice"""

        lookup_flds = []
        for v in self.master.fields.keys():
            if self.master.fields[v]['fkey'] and v.endswith('_id'):
                lookup_flds.append(v)

        ## SqlMask
        if isinstance(self.master, sqlkit.SqlMask):
            data = self.master.sqlData.get()
            if data == None:
                return None

            for key in lookup_flds:
                try:
                    data[key] = self.master.completion._lookup_value(
                            key, data[key])
                except Exception, e:
                    print e
                    pass


            page.add(data)
            return True

        else:
            ## SqlTable
            for diz in self.master.sqlData.all_as_dicts():
                for key in lookup_flds:
                    try:
                        diz[key] = self.master.completion._lookup_value(
                            key, diz[key])
                    except Exception, e:
                        print e
                        pass
                    
                page.add(diz)
            return True

    def on_record_clear(self, new, old):
        pass
    
    def on_reload(self, new, old):
        pass
    def on_completion(self, new, field_name):
        """Adds a constraint to the completion. Must return a tuple:
        ('SQL STATEMET', params). params must be a dict
        """
        return ('',{})


def set_template_dir(dir):
    global print_template_dir
    print_template_dir = dir
