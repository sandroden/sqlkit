import re
import gtk
import completion
from sqlkit.layout import layout, misc
from sqlkit import debug as dbg
from sqlkit.db.utils import tables, get_description
import sqlalchemy
from sqlalchemy.sql import select
import sqlkit 
from datetime import *
from sqlkit.db.django_syntax import django2components

class SqlDataFixNeeded(Exception): pass

class FilterPanel(object):
    """A filter panel has 'entry|operator|string' rows

    the user must be able to enter filter conditions on each operator or add
    filter on the same field 
    """

    def __init__(self, master, visible=True):
        
        """constructor need to know who is the 'master' ie the widget (a mask
        or a table instance) that will display the result. 

        The filter for a SqlMask has a TreeView to show the results and to easy
        browse them.

        """
        self.master = master
        self.get_layout(visible=visible)
        self.row = 0  # counter for position of fields
        self.default_reload = True
        
        self.search_filter_widgets = []         ## list of FIlterWidgets instances
        self.search_filter_field_names = []     ## field_names used
        self.bind_name = self.master.metadata.bind.name
        
    def __del__(self):
        self.destroy()
        
    def get_layout(self, visible=True):
        """create the filter panel widget"""
        if isinstance(self.master, sqlkit.SqlMask):
            lay = """
            {H.a {B m=opts } {O.a tb=gtk-refresh ts=limit tb=gtk-close } }
            {N %filter
               {|T.fld }
               %output
               { TVS=out}
            }
            """
        else:
            lay = """
            {H.a {B m=opts } {O.a tb=gtk-refresh ts=limit tb=gtk-close } }
               {|T.fld }

            """
        self.l = layout.Layout(lay, title='Filter Panel', opts="s")
        self.l.prop('Window', 'visible', visible)
        self.l.prop('O.a', 'show_arrow', 'FALSE')
        self.l.prop('A=.fld', 'yscale', '0')
        self.l.elements['H.a'].pack_properties['y-options'] = ''
        self.l.prop('O.a', 'toolbar_style', 'gtk.TOOLBAR_ICONS')
        self.w = self.l.show(x=self.hide)
#        self.w['s=limit'].set_value(self.master.limit)
        adj = self.w['s=limit'].get_adjustment()
        adj.set_all(self.master.limit, 0, 10000, 10, 100, 100)
        self.l.menu('m=opts',
                    ('-', ),
                    ('gtk-close', 'activate', self.hide),
                    )
        self.l.connect(
            ('tb=gtk-close', 'clicked', self.hide),
            ('tb=gtk-refresh', 'clicked', self.reload_cb)
                        )
        self.w['label-cursor'] = gtk.gdk.Cursor(gtk.gdk.HAND1)
        #self.l.xml('/tmp/f.glade')
        if 'TV=out' in self.w: 
            self.easytv = misc.EasyTreeView(
                ['id', 'output'], tv=self.w['TV=out'], )
            self.selection = self.easytv.tv.get_selection()
            self.selection.connect('changed',self.on_selection_changed)
            self.model = self.easytv.tv.get_model()
            self.easytv.tvc['id'].set_property('visible', False)

    def add_filter(self, active=True, **kwargs):
        """
        add a filter using django-like syntax

        """
        for key, val in kwargs.iteritems():
            path, op, col, op_str, value = django2components(self.master.mapper, {key: val})
            master = self.get_related_master(self.master, path)
            filter_widget = self.add(None, None, col.name, master, force=True)
            filter_widget.check_button.set_active(active)
            if value and not value is True:
                filter_widget.field_widget.set_text(value)
            self.set_operator(filter_widget, op, value)

    def set_operator(self, filter_widget, op, value):
        """
        Set the active operator entry in ComboBox for operator choice
        """
        model = filter_widget.operator.get_model()
        operator_list = [model.get_value(row.iter,0) for row in model]
        if op == 'IS NULL' and value is False:
            op = 'IS NOT NULL'
        try:
            index = operator_list.index(op.upper())
            filter_widget.operator.set_active(index)
        except ValueError, e:
            print e
            pass

    def get_related_master(self, master, path=None):
        """
        Return the SqlWidget that manages the data at 'path'.
        E.g.: if the mapper is the one for movie, and the 'path'  is 'genres'
        as in the doc example, ``get_master``  would return the SqlTable that
        manages the collection of records returned by the relation 'genres'
        """

        for elem in path:
            master = master.related[elem]
        return master


    def add(self, wdg, ev, field_name, master, after=None, show=True, force=False, value=None):
        """add a FilterWidget to the filter panel + operator and string entry
        after: entry will be positioned after widget 'after'
        """
        ## FIXME: after and show?
        search_path = "%s__%s" % (master.relationship_path, field_name)
        if not search_path in self.search_filter_field_names or force:
            widget = get_filter_widget(field_name, self, master, value)
            widget.build_layout(field_name)
            self.search_filter_widgets += [ widget]
            self.search_filter_field_names  += [search_path]

        if 'N.0' in self.w:
            self.w['N.0'].set_current_page(0)

        if show:
            self.w['Window'].show_all()
        self.w['Window'].present()
        try:
            return widget
        except:
            return None

    def hide(self, wid, ev=None):
        """hide FilterPanel."""

        self.w['Window'].set_property('visible', False)
        return True  # stops further processing...
    
    def destroy(self):
        self.w['Window'].destroy()
    
##### reload & TreeView
    def reload_cb(self, widget):
        """issue a reload operation on master. Call back of reload button"""
        length = 0
        if 'TV=out' in self.w:
            display = False
        else:
            display = True
            
        if self.default_reload:
            length = self.master.reload(limit=self.get_limit(), display=display )

        else:
            ## FIXME: sqlData no longe exists
            ## we get here if we use set_reload
            raise SqlDataFixNeeded()
            res = self.master.session.query(self.mapper).select(
                sql[0], params=sql[1], limit=self.get_limit())
            #self.sqlData = sk.sqldata.SqlData(res, self.map_fields,
            #                                  self.master.session)

        if 'TV=out' in self.w:
            if length:
                self.fill_model()
                self.w['N.0'].set_current_page(1)
                self.master.record_display(0)
            
    def set_reload(self, mapper=None, join=None, tables=None):
        """A different method to filter & select is provided
        the scenario is that you have many synced sqlwidgets, you want to provide the
        possibility to select a record in a table with different records in other
        tables and be able to select one particular pair of them from the
        filter tree.

        You need to pass a join to issue the select on and a method in
        actions called 'on_filter_reload' to wich is passed only an
        argument: a dictionary with all the attributes of the collected
        record.

        If you pass tables to set_reload, each table is autoloaded and joined
        to the preceding. The returned join is used.
        
        """
        self.default_reload = False

        if tables:
            if isinstance(tables, str):
                T = {}
                tables = re.split('[ ,]+',tables)
                for tbl in tables:
                    T[tbl] = sqlalchemy.Table(
                        tbl, self.master.metadata, autoload=True)

                for tbl in tables[1:]:
                    join = T[tables[0]].join(T[tbl])
                
        if join:
            class Join(object): pass
            mapper = sqlalchemy.mapper(Join, join)

        self.mapper = mapper
        self.map_fields = sqlkit.minspect.InspectMapper(mapper)

    def fill_model(self):
        """Fill the treeview with a clickable list 

        Fill the model of the treeview that holds the data
        """

        table = self.master.fields.get_primary_table(name=False)
        format_string = get_description(table, attr='format')
        description = tables[table.name].description

        self.model.clear()
        iter = {}
        i = 0
        for obj in self.master.records:
            attr_value = getattr(obj, description)
            if attr_value not in iter:
                iterR = self.model.append(None)
                self.model.set(iterR,
                               0, i,
#                               1, format_string % vars(obj),
                               1, str(obj),
                               )
                iter[attr_value] = iterR
            else:
                iterR = self.model.append(iter[attr_value])
                self.model.set(iterR,
                               0, i,
#                               1, format_string % vars(obj),
                               1, str(obj),
                               )
            i += 1

        self.tv_resize()

    def tv_resize(self):
        tv = self.w['TV=out']
        tv.realize()
        X, Y, width, height, bit = tv.window.get_geometry()
        if height < 100:
            tv.set_property('height-request', 300)
            
    def on_selection_changed(self, *args):
        # when clicking om the teeview we get 2 args: treeView, event
        # when changing selection we only have 1 arg: gtk.treeSelection
        # when clicking 'Refresh' we get e gtk.TreeSelection but no
        #      iter get selected

        ## first guess: we selected w/ pointer
        model, iter = self.selection.get_selected()

        ## we don't have a selection
        if iter is None:
            try:
                ## we moved along the treeview w/ arrows
                wdg, ev = args
                path = wdg.get_path_at_pos(int(ev.x), int(ev.y))[0]
                iter = model.get_iter(path)
            except (ValueError, TypeError), e:
                ## ValueError: deselecting when clicking 'reload'
                ## TypeError: no data in the treeview
                return
            
        idx = self.model.get_value(iter, 0)
        if self.default_reload:
            self.master.record_display(index=int(idx))
        else:
            ## FIXME: this is a not supported configuration at the  moment
            ## when set_reload is used
            ## sqlData is local to panel filter in this situation!
            raise SqlDataFixNeeded()
            self.master.actions.on_filter_reload(self.sqlData.get(index=int(idx)))
    
##### SQL
    def get_limit(self):
        """
        Get limits of the select we are issuing
        """
        self.w['s=limit'].update()
        return  self.w['s=limit'].get_value_as_int()
    
    def add_filter_conditions(self, query):
        """Adds to the query all filter conditions
        """
        
        for pwidget in self.search_filter_widgets:
            query = pwidget.add_filter_condition(query)

        return  query


    def sql_dbg(self, bool_conds):
        for c in bool_conds:
            print "DBG: ", c.left, c.operator, c.right
        

class FilterWidget(object):
    STR_STD_OPERATORS = [ 'LIKE', 'NOT LIKE' ]
    NULL_OPERATORS = [ 'IS NULL', 'IS NOT NULL' ]
    STD_OPERATORS = [ '>=','<=', '=', '!=', '>', '<', ] + NULL_OPERATORS

    def __init__(self, field_name, panel, master):

        self.panel = panel
        self.master = master
        self.field_name = field_name
        self.db_spec = self.master.fields[field_name]
        self.col = self.db_spec['col']
        self.table = self.db_spec['table']
        self.bind_name = self.master.metadata.bind.name


##### handling
    def get_suitable_operators(self):
        """return list of operators meaningfull for engine/data type
        """
        return self.STD_OPERATORS

    def build_layout(self, field_name, after=None, show=True, force=False, ):
        """
        build the gtk interface of this widget
        """

        ## I'd like *not* to .present the widget for any successive field added
        ## but I have not been able to get focus on the window w/o .present()
        
        operators = self.get_suitable_operators()

        ## labels
        self.field_name_event_box = gtk.EventBox()
        self.field_label           = gtk.Label(layout.get_label(field_name))
        self.check_button         = gtk.CheckButton()

        self.check_button.set_active(True)
        self.panel.l.tooltips.set_tip(self.check_button, "Check me to use this filter")
        
        self.field_name_event_box.add(self.field_label)
        self.field_label.set_property('xalign', 0)
        self.field_name_event_box.connect('button-press-event', self.pop_menu, 1)
        #field_name_event_box.window.set_cursor(self.w['label-cursor'])

        ## combo for operator
        self.operator = gtk.combo_box_new_text()
        for op in operators:
            self.operator.append_text(op)
        self.operator.set_active(0)
        #operator.set_property('can_focus', False)

        ## get_active_text per riprenderlo...
        ## entry

        self.field_widget = gtk.Entry()
        self.field_widget.connect('activate', self.panel.reload_cb)

        self.menu = gtk.Menu()
        ## add another filter
        item = gtk.MenuItem(label="Add a new filter on this %s" % self.field_name)
        item.connect('activate', self.add_filter_cb)
        self.menu.append(item)
        self.menu.show_all()
            
        

        Tbl = self.panel.w['T.fld']
        r = self.panel.row
        c = 0
        widgets = [ self.field_name_event_box, self.operator, self.check_button ]
        ftype  = self.master.get_field_type(field_name)
        if not issubclass(ftype, bool):
            widgets += [self.field_widget]
            
        for wdg in widgets:
            Tbl.attach(wdg, c, c+1, r, r+1, xpadding=4)
            c += 1
        self.panel.row += 1
        Tbl.show_all()
        self.field_widget.grab_focus()
        

    
    def add_filter_condition(self, query):
        if not self.check_button.get_active():
            return query
        
        op_value = self.operator.get_active_text()
                
        if op_value in ('IS NULL', 'IS NOT NULL', 'IS TRUE', 'IS FALSE'):
            query = query.filter("%s %s" % (self.field_name, op_value))
            #ret += [ "%s %s" % (self.field_name, op_value) ]
        else:
            value = self.field_widget.get_text()
            if value:
                query = self._compose_field_whereclause(query, value, op_value)
        return query
        

    def _compose_field_whereclause(self, query, value, op_value):
        """return a sql whereclause for field

        """
        
        if self.bind_name == "sqlite" and op_value == "MATCH":
            op_value = 'LIKE'
            value = '%' + value + '%'

        query = query.reset_joinpoint()

        if self.master.relationship_path:
            query = query.join(self.master.relationship_path)
            
        return query.filter(self.col.op(op_value)(value))

    def add_filter_cb(self, menuitem, ):
        self.panel.add(None, None, self.field_name, self.master, force=True)
        
    def pop_menu(self, wdg, ev, num_button):
        #dbg.write(wdg, ev, num_button)
        if ev.button == num_button:
            self.menu.popup(None, None, None, ev.button, ev.time )
        
    

class FilterStringWidget(FilterWidget):

    def get_suitable_operators(self ):
        if self.bind_name in 'sqlite':
            return ['MATCH'] + self.STR_STD_OPERATORS + self.STD_OPERATORS
        
        elif self.bind_name in 'mysql':
            return [ 'REGEXP' ] + self.STD_OPERATORS

        elif self.bind_name in 'postgres':
            return  ['~*', '~', '!~*', '~*' ] + self.STD_OPERATORS


class FilterBooleanWidget(FilterWidget):

    def get_suitable_operators(self):
        return [ 'IS TRUE', 'IS FALSE' ] + self.NULL_OPERATORS

class FilterDateWidget(FilterWidget):


    def _compose_field_whereclause(self, query, value, op_value):
        """Implement the mini date algebra to allow for relative dates
        see dry.dateutils

        """

        from dry.dateutils import string2dates
        start, stop = string2dates(value)

        # If 'stop' is not None it means I have a period (eg.: 'y > M')
        # and I use operators to delimit this
        # period ignoring the operator from the widget
                        
        op_value = self.operator.get_active_text()
        if not stop:
            query = query.filter(self.col.op(op_value)(start))
        else:
            ## start
            query = query.filter(self.col.op(">=")(start))
            ## stop
            query = query.filter(self.col.op("<=")(stop))
            #ret += [self.col.op("<=")(stop)]

        return  query

class FilterFKeyWidget(FilterWidget):

    def __init__(self, field_name, panel, master):

        FilterWidget.__init__(self, field_name, panel, master)

        from sqlkit.db.minspect import get_foreign_info

        foreign_keys = self.master.fields[self.field_name]['fkey']
        self.ftable, self.fcol = get_foreign_info(foreign_keys, names=False)

    def get_suitable_operators(self):

        if self.bind_name in ('postgres'):
            return  ['~*', '~', '!~*', '~*' ] + self.STD_OPERATORS

        elif self.bind_name in ('mysql'):
            return ['REGEXP' ] + self.STD_OPERATORS

        elif self.bind_name in ('sqlite'):
            return ['MATCH' ] + self.STD_OPERATORS

    def _compose_field_whereclause(self, query, value, op_value):
        """return a sql whereclause for field

        In case field is a fkey, and the destination lookup field is not in
        the mapper, it composes a subselect
        """
        if self.bind_name == "sqlite" and op_value == "MATCH":
            op_value = 'LIKE'
            value = '%' + value + '%'

        fdescr = get_description(self.ftable, attr='description')

        ids = select([self.fcol], self.ftable.columns[fdescr].op(op_value)(value))
        query = query.reset_joinpoint()

        if self.master.relationship_path:
            query = query.join(self.master.relationship_path)

        return query.filter(self.col.in_(ids))


def get_filter_widget(field_name, panel, master, value=None):
    """
    return an instance of a proper FilterWidget according to type
    """

    args = field_name, panel, master
    if master.is_date(field_name) or master.is_datetime(field_name):
        return FilterDateWidget(*args)

    elif master.is_fkey(field_name):
        return FilterFKeyWidget(*args)

    elif master.is_boolean(field_name):
        return FilterBooleanWidget(*args)
    
    elif master.is_number(field_name):
        return FilterWidget(*args)
    
    else:
        return FilterStringWidget(*args)
        


