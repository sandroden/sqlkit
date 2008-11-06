from sqlkit import debug as dbg
from sqlkit import layout, SqlTable, SqlMask
import sqlkit
import sqlalchemy as sa
import gtk
import re

class TableBrowser(object):
    def __init__(self, dbproxy, title=None, opts=None, x=None):
        lay = """ {O tb=gtk-quit tb=gtk-refresh }
                   {- b=filter_tables e=filter}
                   TVS=tree"""
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
        cols = ['table', 'def', 'pkey', 'fkey']
        self.stv = layout.misc.EasyTreeView(cols, tv=self.tv)
        self.model = self.tv.get_model()
        #self.configure_treeview(self.tv)
        self.tv.connect('button-press-event', self.popup_col_menu)
        self.l.connect(
            ('tb=gtk-quit', 'clicked', self.on_quit),
            ('tb=gtk-refresh', 'clicked', self.reload),
            ('b=filter_tables', 'clicked', self.fill_model),
            ('e=filter', 'activate', self.fill_model),
            )
        self.fill_model()
        self.lay_obj = self.l
        self.widgets = self.w

    def on_quit(self, widget):
        if self.x == 'quit':
            gtk.main_quit()
        else:
            self.widgets['Window'].destroy()
            
    def reload(self, *args):
        dbg.write('reloading sqlkit')
        print reload(sqlkit)
        #reload(sqlkit.sqlwidget)
        print reload(sqlkit.table.table)
        #reload(sqlkit.mask.mask)
        
    def popup_col_menu(self, wdg, ev ):
        try:
            self.w['M=popup'].destroy()
        except:
            pass
        iter = self.model.get_iter(
            wdg.get_path_at_pos(int(ev.x),int(ev.y))[0])
        table = self.model.get_value(iter,0)
        
        #table = self.model.get_value(self.model.get_iter(path), 0)

        
        menu = self.w['M=popup'] = gtk.Menu()

        ## add to filter
        item = gtk.MenuItem(label="mask" )
        item.connect('activate', self.activate_cb, ('mask', table ))
        menu.append(item)

        ## add to filter
        item = gtk.MenuItem(label="table" )
        item.connect('activate', self.activate_cb, ('table', table ))
        menu.append(item)

        ## add to filter
        item = gtk.MenuItem(label="table reflection" )
        item.connect('activate', self.get_table_info_in_model, (table, iter ))
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)

    def activate_cb(self, wdg, data):
        #dbg.write()
        mode, table = data
        options ={'table' : table,
               'dev' : self.opts.dev,
               'single' : False,
               'nick' : "%s_%s" % (table, mode),
               'dbproxy' : self.dbproxy,
           }
        if mode == 'mask':
            try:
                SqlMask(**options)
            except sqlkit.completion.MissingDescriptorField:
                pass
        else:
            try:
                SqlTable(**options)
            except sqlkit.completion.MissingDescriptorField:
                pass
            
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
        #dbg.write(table_name, iter)
        tbl = sa.Table(table_name, self.dbproxy.metadata, autoload=True)
        self.tables[table_name] = tbl
        pks = []
        for pk in tbl.primary_key:
            pks += [pk.name]
        self.model.set(iter, 2, ",".join(pks))
            
        for c in tbl.c:
            col = self.model.append(iter)
            self.model.set(col, 0, c.name )
            self.model.set(col, 1, c.type.get_col_spec())
            if c.primary_key:
                self.model.set(col, 2, 'X' )
            if c.foreign_keys:
                self.model.set(col, 3, repr(c.foreign_keys) )
                

