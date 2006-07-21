import gtk
import layout
import layout.misc
import completion
import dbg
import sqlalchemy
import sqlkit as sk

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
        self.w['s=limit'].set_value(self.master.limit)
        adj = self.w['s=limit'].get_adjustment()
        adj.upper = 10000
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
            
        self.master.reload(sql=sql, limit=self.get_limit(), display=display )

        if 'TV=out' in self.w:
            self.fill_model()
            self.w['N.0'].set_current_page(1)
            
        #dbg.write("%s type: %s" % (bind_params, type(bind_params)))
        #self.master.reload(sql=(sql, bind_params), limit=limit )
        #self.master.record_display()
        #print self.sql()
    
    
    def fill_model(self):
        """Fill the treeview with a clickable list """
        attr = self.master.completion._add_descriptor_fields(
            mode='ret', table_name = self.master.fields.get_primary_table())

        self.model.clear()
        for i, v in enumerate(self.master.sqlData.pointers):
            R = self.master.sqlData.get(index=i)
            self.model.append(None, [i, R[attr]])
            
            
    def tv_changed_cb(self, *args):
        # when clicking om the teeview we get 2 args: treeView, event
        # when changing selection we nly have 1 arg: gtk.treeSelection
        # when clicking 'Refresh' we get e gtk.TreeSelection but no
        #      iter get selected

        model, iter = self.selection.get_selected()
        if not iter:
            try:
                wdg, ev = args
                iter = model.get_iter(wdg.get_path_at_pos(int(ev.x), int(ev.y))[0])
            except ValueError: # deselecting when clicking 'reload'
                return
            
        idx = self.model.get_value(iter, 0)
        self.master.record_display(index=int(idx))

    
##### handling
    def hide(self, wid, ev=None):
        """hide FilterPanel."""
        #print self.w['Window'], "destroy", "wid", wid
        self.w['Window'].set_property('visible', False)
        return True  # stops further processing...
    
    def destroy(self):
        self.w['Window'].destroy()
    
    def add(self, wdg, ev, field, after=None, show=True):
        """this adds a field to the filter panel + operator and string entry
        after: entry will be positioned after widget 'after'
        """
        if ev.button == 3:
            self.w['Window'].present()
            return

        ## labels
        field_name_event_box = gtk.EventBox()
        field_name = gtk.Label(layout.get_label(field))
        field_name_event_box.add(field_name)
        field_name.set_property('xalign', 0)
        field_name_event_box.connect('button-press-event', self.pop_menu,
                                     'show=True')
        #field_name_event_box.window.set_cursor(self.w['label-cursor'])


        ## combo for operator
        operator = gtk.combo_box_new_text()
        operators = ['~*', '~', '=', '!=', '>', '>=','<','<=', 'IS NULL',
                     'IS NOT NULL', 'LIKE' ]
        for op in operators:
            operator.append_text(op)
        operator.set_active(0)
        #operator.set_property('can_focus', False)

        ## get_active_text per riprenderlo...
        ## entry
        field_value = gtk.Entry()
        field_value.connect('activate', self.reload_cb)

        Tbl = self.w['T.fld']
        r = self.row
        c = 0
        for wdg in [ field_name_event_box, operator, field_value ]:
            Tbl.attach(wdg, c, c+1, r, r+1, xpadding=4)
            c += 1
        self.row += 1
        Tbl.show_all()
    
        self.fields.append({
            'field':    field,
            'operator': operator,
            'entry':    field_value
            } )
        if show:
            self.w['Window'].show_all()
    
##### SQL
    def get_limit(self):
        return  self.w['s=limit'].get_value_as_int()
    
    def pop_menu(self, wdg, ev, num_button):
        #print "pop_menu", wdg, ev
        if ev.button == num_button:
            self.w['M=opts'].popup(None, None, None, ev.button, ev.time )
        
    def sql(self):
        """create a sql statement composing all requests
        returns a sql whereclause and a bindparam dictionary
        """
        ret = self.master.fields.get_join_cnd()
        #dbg.write(ret)
        values={}
        for fld in self.fields:
            value = fld['entry'].get_text()
            if len(value) > 0:
                op = fld['operator'].get_active_text()
                fld['op_value'] = op
                if op in ('IS NULL', 'IS NOT NULL'):
                    ret += [ "%(field)s %s" %(fld, op) ]
                else:
                    #values[fld['field']] = value
                    ret += self._compose_field_whereclause(fld, values, value)
                    #ret += [self.master.fields[fld['field']]['col'].op(op)(value)]
        sql = (sqlalchemy.and_(*ret), values)
        #self.sql_dbg(ret)
        #dbg.write(ret)
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
            fld['ftable'], fld['fname'] = info['fkey']
            fld['fdescr'] = self.master.completion._add_descriptor_fields(
                mode='return', table_name=fld['ftable'])

            if fld['fdescr'] in F:
                ## this means we have a mapper that has already this field
                ## we don't need a subselect
                #descr_col = F[fld['fdescr']]['col']
                sql = F[fld['fdescr']]['col'].op(fld['op_value'])(value)
                return [sql]

            if info['fkey']:
                values[fld['field']] = value

                ## FIXME: not using bind parameters
                s = """%(ftable)s.%(fname)s FROM %(ftable)s
                WHERE %(ftable)s.%(fdescr)s %(op_value)s '%(value)s' """ % (fld)
                dbg.write(s)
                ## if this parameters is not deleted, SA will add a condition to
                ## the select to match it
                del values[fld['field']]

#                 s = """%(ftable)s.%(field)s FROM %(ftable)s
#                 WHERE %(ftable)s.%(fdescr)s %(op_value)s :%(fname)s) """ % (fld)

#                 attr_col = F[fld['field']]['col']
#                 descr_col = F[fld['fdescr']]['col']
#                 s = sqlalchemy.select(["%(ftable)s.%(field)s" % fld],
#                                       descr_col.op(fld['op_value'])(value))

                sql = F[fld['field']]['col'].in_(sqlalchemy.select([s]))

        return [ sql ]

#     def _compose_field_whereclause_old(self, fld):
#         """return a sql whereclause for field

#         In case field is a fkey, terminating with _id, and the destination
#         lookup field is not in the mapper, it composes a subselect
#         """
#         sql = "%(field)s %(op_value)s :%(field)s"% (fld)
        
#         if fld['field'].endswith('_id'):
#             info = self.master.fields[fld['field']]
#             fld['fdescr'] = self.master._add_descriptor_fields(
#                 mode='return', table_name='city')
#             if info['fkey']:
#                 fld['ftable'], fld['fname'] = info['fkey']
#                 sql = """%(field)s IN (
#                 SELECT %(field)s FROM %(ftable)s
#                 WHERE %(fdescr)s %(op_value)s :%(fname)s) """ % (fld)

#         return [ sql ]
        
        
