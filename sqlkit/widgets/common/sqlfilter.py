import gtk
from layout import layout
import layout.misc
import completion
import dbg
import re
import sqlalchemy
import sqlkit as sk
from datetime import *

class FilterPanel(object):
    """A filter panel has 'entry|operator|string' rows

    the user must be able to enter filter conditions on each operator or add
    filter on the same field 
    """
    fields = [] # [ { 'field' : 'value', 'operator' : widget, 'entry' : widget }, {...} ]
    def __init__(self, master, visible=True):
        
        """constructor need to know who is the 'master' ie the widget (a mask
        or a table instance) that will display the result"""
        self.master = master
        self.get_layout(visible=visible)
        self.row =0  # counter for position of fields
        self.default_reload = True
        
    def get_layout(self, visible=True):
        """create the filter panel widget"""
        if isinstance(self.master, sk.SqlMask):
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
        self.l = layout.Layout(lay, title='Filter Panel')
        self.l.prop('Window', 'visible', visible)
        self.l.prop('O.a', 'show_arrow', 'FALSE')
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
            self.easytv = layout.misc.EasyTreeView(
                ['id', 'output'], tv=self.w['TV=out'], )
            self.selection = self.easytv.tv.get_selection()
            self.selection.connect('changed',self.tv_changed_cb)
            self.model = self.easytv.tv.get_model()
            self.easytv.tv.connect('button_press_event', self.tv_changed_cb)
            self.easytv.tvc['id'].set_property('visible', False)

##### reload & TreeView
    def reload_cb(self, widget):
        """issue a reload operation on master. Call back of reload button"""
        #sql, bind_params = self.sql()
        sql = self.sql()
        if 'TV=out' in self.w:
            display = False
        else:
            display = True
            
        if self.default_reload:
            dbg.write('default.reload', self.default_reload)
            self.master.reload(sql=sql, limit=self.get_limit(), display=display )
            self.sqlData = self.master.sqlData
        else:
            res = self.master.session.query(self.mapper).select(
                sql[0], params=sql[1], limit=self.get_limit())
            self.sqlData = sk.sqldata.SqlData(res, self.map_fields,
                                              self.master.session)
#            self.sqlData.fields(['user_id','user_name','mail_user_id'])
#            self.sqlData.printall()
        if 'TV=out' in self.w:
            self.fill_model()
            self.w['N.0'].set_current_page(1)
            
        #dbg.write("%s type: %s" % (bind_params, type(bind_params)))
        #self.master.reload(sql=(sql, bind_params), limit=limit )
        #self.master.record_display()
        #print self.sql()
    
    
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
        self.map_fields = sk.minspect.InspectMapper(mapper)
    def fill_model(self):
        """Fill the treeview with a clickable list """
        attr = self.master.completion._add_descriptor_fields(
            mode='ret', referenced_table = self.master.fields.get_primary_table())
        if self.master.filter == True:
            fmt = "%%(%s)s" % attr
        elif isinstance(self.master.filter, list):
            fmt = ["%%(%s)s" % f for f in self.master.filter]
            fmt = " - ".join(fmt)
            attr = self.master.filter[0]
        else:
            fmt = self.master.filter
            

        self.model.clear()
        iter = {}
        for i, v in enumerate(self.sqlData.pointers):
            R = self.sqlData.get(index=i)
            #dbg.write("R", R)
            if R[attr] not in iter:
                iterR = self.model.append(None)
                self.model.set(iterR,
                               0, i,
                               1, fmt % R
                               )
                iter[R[attr]] = iterR
            else:
                iterR = self.model.append(iter[R[attr]])
                self.model.set(iterR,
                               0, i,
                               1, fmt % R
                               )
        
        self.tv_resize()
    def tv_resize(self):
        tv = self.w['TV=out']
        tv.realize()
        X, Y, width, height, bit = tv.window.get_geometry()
        if height < 100:
            tv.set_property('height-request', 300)
            
    def tv_changed_cb(self, *args):
        # when clicking om the teeview we get 2 args: treeView, event
        # when changing selection we only have 1 arg: gtk.treeSelection
        # when clicking 'Refresh' we get e gtk.TreeSelection but no
        #      iter get selected

        ## first guess: we selected w/ pointer
        model, iter = self.selection.get_selected()
        ## we don't have a selection
        if not iter:
            try:
                ## we moved along the treeview w/ arrows
                wdg, ev = args
                iter = model.get_iter(wdg.get_path_at_pos(int(ev.x), int(ev.y))[0])
            except ValueError:
                ## deselecting when clicking 'reload'
                return
            
        idx = self.model.get_value(iter, 0)
        # dbg.write("index=%s" %int(idx))
        if self.default_reload:
            self.master.record_display(index=int(idx))
        else:
            ## sqlData is local to panel filter in this situation!
            self.master.actions.on_filter_reload(self.sqlData.get(index=int(idx)))
    
    def pop_menu(self, wdg, ev, num_button):
        #dbg.write(wdg, ev, num_button)
        if ev.button == num_button:
            self.w['M=opts'].popup(None, None, None, ev.button, ev.time )
        
##### handling
    def hide(self, wid, ev=None):
        """hide FilterPanel."""

        self.w['Window'].set_property('visible', False)
        return True  # stops further processing...
    
    def destroy(self):
        self.w['Window'].destroy()
    
    def get_suitable_operators(self, field_name, ftype, eng_type):
        """return list of operators meaningfull for engine/data type
        """
        #dbg.write( field_name, ftype, eng_type)

        STR_STD_OPERATORS = [ 'LIKE', 'NOT LIKE' ]
        NULL_OPERATORS = [ 'IS NULL', 'IS NOT NULL' ]
        STD_OPERATORS = [ '=', '!=', '>', '>=','<','<=', ] + NULL_OPERATORS
        BOOLEAN_OPERATORS = [ 'IS TRUE', 'IS FALSE' ] + NULL_OPERATORS
        #import pdb; pdb.set_trace()
        if issubclass(ftype, bool):
            dbg.write('bool')
            return BOOLEAN_OPERATORS
        
        if issubclass(ftype, (int, float, datetime, date, time)):
            return STD_OPERATORS

        if eng_type in 'sqlite':
            return STR_STD_OPERATORS + STD_OPERATORS
        
        elif eng_type in 'mysql':
            return [ 'REGEXP' ] + STD_OPERATORS

        elif eng_type in 'postgres':
            return  ['~*', '~', '!~*', '~*' ] + STD_OPERATORS

    

    def add(self, wdg, ev, field, after=None, show=True):
        """add a field to the filter panel + operator and string entry
        after: entry will be positioned after widget 'after'
        """
        if ev.button == 3:
            self.w['Window'].present()
            self.w['Window'].deiconify()
            return

        eng_type = self.master.metadata.bind.name
        ftype = self.master.fields[field]['type']
        operators = self.get_suitable_operators(field, ftype, eng_type)

        ## labels
        field_name_event_box = gtk.EventBox()
        field_name           = gtk.Label(layout.get_label(field))
        check_button         = gtk.CheckButton()

        check_button.set_active(True)
        self.l.tooltips.set_tip(check_button, "Check me to use this filter")
        
        field_name_event_box.add(field_name)
        field_name.set_property('xalign', 0)
        field_name_event_box.connect('button-press-event', self.pop_menu,
                                     'show=True')
        #field_name_event_box.window.set_cursor(self.w['label-cursor'])

        ## combo for operator
        operator = gtk.combo_box_new_text()
        for op in operators:
            operator.append_text(op)
        operator.set_active(0)
        #operator.set_property('can_focus', False)

        ## get_active_text per riprenderlo...
        ## entry

        field_widget = gtk.Entry()
        field_widget.connect('activate', self.reload_cb)

        Tbl = self.w['T.fld']
        r = self.row
        c = 0
        widgets = [ field_name_event_box, operator, check_button ]
        if not issubclass(ftype, bool):
            widgets += [field_widget]
            
        for wdg in widgets:
            Tbl.attach(wdg, c, c+1, r, r+1, xpadding=4)
            c += 1
        self.row += 1
        Tbl.show_all()

        self.fields.append({
            'field':    field,
            'type' :    ftype,
            'operator': operator,
            'entry':    field_widget,
            'check_button': check_button,
            } )
        if show:
            self.w['Window'].show_all()

    
##### SQL
    def get_limit(self):
        self.w['s=limit'].update()
        return  self.w['s=limit'].get_value_as_int()
    
    def sql(self):
        """create a sql statement composing all requests
        returns a sql whereclause and a bindparam dictionary
        """
        ret = self.master.fields.get_join_cnd()
        #dbg.write(ret)
        values={}
        for fld in self.fields:
            if fld['check_button'].get_active():
                op = fld['operator'].get_active_text()
                fld['op_value'] = op
                
                if op in ('IS NULL', 'IS NOT NULL', 'IS TRUE', 'IS FALSE'):
                    ret += [ "%(field)s %(op_value)s" % fld ]
                else:
                    value = fld['entry'].get_text()
                    if value:
                        ret += self._compose_field_whereclause(
                            fld, values, value)

        sql = (sqlalchemy.and_(*ret), values)
        #self.sql_dbg(ret)
        #dbg.write(values)
        return sql
    
    def sql_dbg(self, bool_conds):
        for c in bool_conds:
            print "DBG: ", c.left, c.operator, c.right
        
    def _compose_field_whereclause(self, fld, values, value):
        """return a sql whereclause for field

        In case field is a fkey, terminating with _id, and the destination
        lookup field is not in the mapper, it composes a subselect
        """
        F = self.master.fields
        fld['value'] = value
        sql = F[fld['field']]['col'].op(fld['op_value'])(value)
        #dbg.write(fld)
        info = self.master.fields[fld['field']]
        if fld['field'].endswith('_id') and info['fkey']:
            fld['ftable'], fld['fname'] = self.master.completion.get_foreign_info(fld['field'])
            fld['fdescr'] = self.master.completion._add_descriptor_fields(
                mode='return', referenced_table=fld['ftable'])

            if fld['fdescr'] in F:
                ## this means we have a mapper that has already this field
                ## we don't need a subselect
                #descr_col = F[fld['fdescr']]['col']
                dbg.write("qui 1")
                sql = F[fld['fdescr']]['col'].op(fld['op_value'])(value)
                return [sql]

            if info['fkey']:
                dbg.write("qui 2")
                values[fld['field']] = value

                ## FIXME: not using bind parameters
                s = """%(ftable)s.%(fname)s FROM %(ftable)s
                WHERE %(ftable)s.%(fdescr)s %(op_value)s '%(value)s' """ % (fld)
                dbg.write(s)
                ## if this parameters is not deleted, SA will add a condition to
                ## the select to match it
                del values[fld['field']]

                sql = F[fld['field']]['col'].in_(sqlalchemy.select([s]))

        return [ sql ]

