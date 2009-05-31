from sqlkit import debug as dbg, _
from sqlkit.widgets import SqlTable, SqlMask
from sqlkit import layout
from sqlkit.db import utils
import sqlkit
import sqlalchemy as sa
import gtk
import re

GENERAL_UI = '''
  <menubar name="Main">
     <menu action="Database">
        <menuitem action="EditFields"/>
        <separator name="sep1"/>
        <menuitem action="Quit"/>
     </menu>
     <menu action="Modify">
        <menuitem action="Reload"/> 
        <menuitem action="Dev"/>
    </menu>
     <menu action="Help">
        <menuitem action="About"/>
     </menu>
  </menubar>
  <toolbar name="TbMain">
    <toolitem  action="Quit" />
    <toolitem  action="Dev" />
    <toolitem  action="Reload" />
  </toolbar>
'''

class TableBrowser(object):
    def __init__(self, dbproxy, title=None, opts=None, x=None):

        lay = """
             {V.menu }
             {- b=filter_tables e=filter}
             TVS=tree

        """
        self.tables = {}
        self.x = x
        if opts:
            self.opts = opts
        else:
            class Opts: pass
            opts = Opts()
            opts.dev = False
            opts.all_tables = None
            self.opts = opts
            
        self.dbproxy = dbproxy
        self.l = layout.Layout(lay, title=title, opts='-')
        self.l.pack(
            ## fill is just to avoid default that is expand
            ('T.0',             'y-options', 'fill'),
            ('b=filter_tables', 'x-options', 'fill'),
            )
        self.w = self.l.show()
        self.tv = self.w['TV=tree']
        cols = ['table', 'def', 'pkey', 'fkey', 'nullable', 'indexes']
        self.stv = layout.misc.EasyTreeView(cols, tv=self.tv)
        self.model = self.tv.get_model()
        #self.configure_treeview(self.tv)
        self.tv.connect('button-press-event', self.popup_col_menu)
        self.l.connect(
#            ('tb=gtk-quit', 'clicked', self.quit_cb),
#            ('tb=gtk-refresh', 'clicked', self.reload),
            ('b=filter_tables', 'clicked', self.fill_model),
            ('e=filter', 'activate', self.fill_model),
            )
        self.fill_model()
        self.lay_obj = self.l
        self.widgets = self.w
        self.set_actions()
        self.prepare_uimanager()
        self.add_accelerators()

        from sqlkit.widgets.table.utils import set_height_request
        set_height_request(self.tv, rows=min(30, len(self.model)))

    def set_actions(self):
        self.actiongroup  = gtk.ActionGroup('Main')
        self.actiongroup.add_actions([
            ('Database', None, _('Database')),
            ('Modify', None, _('Modify')),
            ('Help', None, _('Help')),
            ('Quit', gtk.STOCK_QUIT, None, '<Ctrl>q', None, self.quit_cb),
            ('About', gtk.STOCK_ABOUT, None, None, None, self.about_dialog_cb),
            ])
        tooltip = """Configure the fields: \nlabels, tooltip, completion, search field"""

        self.actiongroup.add_actions([
            ('EditFields', None, 'Edit Sqlkit Fields', '<Ctrl>e', tooltip, sqlkit_model),
            ], self.dbproxy)
        self.actiongroup.add_toggle_actions([
            ('Dev', None, 'Primary Key', None, 'Show/Hide primary key if the key is numeric',
             self.toggle_dev_cb),
            ('Reload', None, 'Load', None, 'Load the data as well', self.toggle_reload_cb),
            ])

    def toggle_reload_cb(self, item):
        pass

    def toggle_dev_cb(self, item):
        pass
            
    def prepare_uimanager(self):

        self.ui_manager = gtk.UIManager()
        self.accel_group = self.ui_manager.get_accel_group()
        self.ui_manager.add_ui_from_string(GENERAL_UI)
        self.w['Window'].add_accel_group(self.accel_group)
        self.ui_manager.insert_action_group(self.actiongroup, 0)
        header = self.w['V.menu']
        menu    = self.ui_manager.get_widget('/Main')
        tools    = self.ui_manager.get_widget('/TbMain')
        header.add(menu)
        header.add(tools)
        
    def add_accelerators(self):
        """Add accelerators: now Ctrl-l"""

        # key accelerators
        self.accel_group.connect_group(ord('l'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.focus_filter)
        self.accel_group.connect_group(ord('f'), 
                                       gtk.gdk.CONTROL_MASK, 
                                       gtk.ACCEL_LOCKED, 
                                       self.focus_filter)
            
    def focus_filter(self, *args):
        self.widgets['e=filter'].grab_focus()

    def quit_cb(self, widget):
        if self.x == 'quit':
            gtk.main_quit()
        else:
            self.widgets['Window'].destroy()
            
    def reload(self, *args):
        dbg.write('reloading sqlkit')
        #print reload(sqlkit)
        #reload(sqlkit.sqlwidget)
        #print reload(sqlkit.table.table)
        #reload(sqlkit.mask.mask)
        
    def popup_col_menu(self, wdg, ev ):
        try:
            self.w['M=popup'].destroy()
        except:
            pass
        iter = self.model.get_iter(
            wdg.get_path_at_pos(int(ev.x),int(ev.y))[0])
        if self.model.iter_parent(iter):
            return
        table = self.model.get_value(iter,0)
        
        #table = self.model.get_value(self.model.get_iter(path), 0)

        
        menu = self.w['M=popup'] = gtk.Menu()

        ## add to filter
        item = gtk.MenuItem(label=_("Mask") )
        item.connect('activate', self.activate_cb, ('mask', table ))
        menu.append(item)

        ## add to filter
        item = gtk.MenuItem(label=_("Table") )
        item.connect('activate', self.activate_cb, ('table', table ))
        menu.append(item)

        if not self.model.iter_children(iter):
            ## add to filter
            item = gtk.MenuItem(label=_("Table reflection") )
            item.connect('activate', self.get_table_info_in_model, (table, iter ))
            menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)

    def activate_cb(self, wdg, data):

        mode, table = data
        dev = self.ui_manager.get_action('/Main/Modify/Dev').get_active()
        options ={'table' : table,
               'dev' : dev,
               'single' : False,
               'nick' : "%s_%s" % (table, mode),
               'dbproxy' : self.dbproxy,
           }
        if mode == 'mask':
            SqlWid = SqlMask
        else:
            SqlWid = SqlTable

        try:
            self.t = SqlWid(**options)
            if self.ui_manager.get_action('/Main/Modify/Reload').get_active():
                self.t.reload()
        except sqlkit.exc.MissingDescriptorField:
            pass
        except sqlkit.exc.MissingPrimaryKey, e:
            dialog, l = self.l.dialog(type='ok', lay="l=msg", text=e.message)
            dialog.show_all()
            response = dialog.run()
            dialog.destroy()
    
    def skip_table(self, table):
        """ this is just for skipping, must return True"""
        
        if self.dbproxy.metadata.bind.name == 'postgres' and table.startswith('pg_'):
            return True
        if not re.search(TABLE_MATCH, table):
            return True

    def fill_model(self, *args):
        """called by button filter_table and filter entry"""
        global TABLE_MATCH
        self.model.clear()
        TABLE_MATCH = self.w['e=filter'].get_text() or ".*"
        tables = self.dbproxy.metadata.bind.table_names()
        tables.sort()
        for table in tables:
            if self.skip_table(table):
                continue
            iter = self.model.append(None)
            self.model.set(iter, 0, table)
            if self.opts.all_tables:
                self.get_table_info_in_model(None, (table, iter))

    def get_table_info_in_model(self, junk, (table_name, iter)):
        """
        fill the model relative to info on table 
        """
        
        tbl = sa.Table(table_name, self.dbproxy.metadata, autoload=True)
        index_dict = {}
        self.tables[table_name] = tbl
        pks = []
        for pk in tbl.primary_key:
            pks += [pk.name]

        ## 
        for i, index in enumerate(tbl.indexes):
            for j, col in enumerate(index.columns):
                # show order of column in index
                if not col.name in index_dict:
                    index_dict[col.name] = []
                index_dict[col.name] += [index.unique and 'UNIQUE_%s.%s' % (i, j) or 'IDX_%s.%s' % (i,j)]

        self.model.set(iter, 2, ",".join(pks))
            
        for c in tbl.c:
            col = self.model.append(iter)
            self.model.set(col, 0, c.name )
            self.model.set(col, 1, c.type.get_col_spec())
            if c.primary_key:
                self.model.set(col, 2, 'X' )
            if c.foreign_keys:
                self.model.set(col, 3, repr(c.foreign_keys) )
            if not c.nullable:
                self.model.set(col, 4, "NOT NULL")
            if c.name in index_dict:
                self.model.set(col, 5, " ".join(index_dict[c.name]))

        path = self.model.get_path(iter)
        self.tv.expand_row(path, True)
                

        
    def about_dialog_cb(self, menuItem):
        """
        The about dialog
        """
        dialog = create_about_dialog()
        dialog.run()
        dialog.destroy()
        

def sqlkit_model(item=None, dbproxy=None):
    lay = """
       name
       search_field
       format
       o2m=attributes -

    """
    global tbl
    if dbproxy:
        db = dbproxy
    try:
        from sqlkit.db.sqlkit_model import SqlkitTable, Base
        Base.metadata.bind = db.metadata.bind
        if not db.metadata.bind.has_table('_sqlkit_table'):
            response = dialog_create_continue()
            if response == gtk.RESPONSE_CANCEL:
                sys.exit(0)
            else:    
                Base.metadata.create_all()
                
        tbl = SqlMask(class_=SqlkitTable, dbproxy=db, single=not bool(dbproxy),
                      hooks=ConfigHook(), layout=lay)
        
    except Exception, e:
        print e
        raise

def dialog_create_continue():
    dialog = gtk.Dialog("Creating sqlkit tables", None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_OK, gtk.RESPONSE_OK,
                         gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    label = gtk.Label("No sqlkit tables are present: I'll proceed creating them")
    dialog.vbox.add(label)
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    return response


def create_about_dialog():
    """
    Create a default AboutDialog
    """
    def func(dialog, link, user_data):
        import webbrowser
        webbrowser.open(link)

    about_dialog = gtk.AboutDialog()
    gtk.about_dialog_set_url_hook(func, None)
    about_dialog.set_authors(["Sandro Dentella <sandro@e-den.it>"])
    about_dialog.set_license("GPL v.3")
    about_dialog.set_version(sqlkit.__version__)
    about_dialog.set_name("sqlkit")
    about_dialog.set_website("http://sqlkit.argolinux.org")
    about_dialog.set_website_label("http://sqlkit.argolinux.org")
    return about_dialog

def open_sqlwidget(table, single, opts, db):

    options ={'table' : table,
              'dev' : opts.dev,
              'single' : single,
              'nick' : table,
              'dbproxy' : db,
              'sql' : opts.sql,
              'field_list' : opts.field_list,
              'order_by' : opts.order_by,
           }
    if opts.mask:
        try:
            SqlMask(**options)
        except sqlkit.exc.MissingDescriptorField:
            pass

    else:
        try:
            SqlTable(**options)
        except sqlkit.exc.MissingDescriptorField:
            pass
            

class ConfigHook(object):

    def on_init(self, m):
        self.m = m
        self.db = m.dbproxy
        m.completions.name.set_values(self.db.metadata.bind.table_names())
        m.completions.name.autostart = 1

        
        m.completions.search_field.set_values(self.get_names)
        m.completions.search_field.autostart = 1
        m.related.attributes.completions.name.set_values(self.get_all_names)
        m.related.attributes.completions.name.autostart = 1

    def get_names(self, values = None):
        table = self.m.get_value('name')
        if table:
            cols = utils.get_fields(table, metadata=self.db.metadata, name=False)
            return [c.name for c in cols if isinstance(c.type, (sa.String, sa.Text))]
        else:
            return []

    def get_all_names(self, values = None):
        table = self.m.get_value('name')
        if table:
            return utils.get_fields(table, metadata=self.db.metadata, name=True)
        else:
            return []

