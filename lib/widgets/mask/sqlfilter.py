import gtk
import layout

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
        self._create_window(visible=visible)
        self.row =0  # counter for position of fileds

    def reload_cb(self, widget):
        """issue a reload operation on master. Call back of reload button"""
        sql, bind_params = self.sql()
        print "reload_cb: %s type: %s" % (bind_params, type(bind_params))
        self.master.reload(sql=(sql, bind_params) )
        #self.master.record_display()
        #print self.sql()

    def _create_window(self, visible=True):
        """create the filter panel widget"""
        lay = """
        {H {B m=opts } {O.a tb=gtk-refresh ts=limit tb=gtk-close } }
        {|T.fld }
        """
        self.l = layout.Layout(lay, title='Filter Panel')
        self.l.prop('Window', 'visible', visible)
        self.l.prop('O.a', 'show_arrow', 'FALSE')
        self.l.prop('O.a', 'toolbar_style', 'gtk.TOOLBAR_ICONS')
        self.w = self.l.show(x=self.hide)
        self.w['s=limit'].set_value(100)
        self.l.menu('m=opts',
                    ('-', None,),
                    ('gtk-close', self.hide),
                    )
        self.l.connect(
            ('tb=gtk-close', 'clicked', self.hide),
            ('tb=gtk-refresh', 'clicked', self.reload_cb)
                        )
        self.l.xml('/tmp/f.glade')
        
    def hide(self, wid, ev=None):
        """hide FilterPanel."""
        print self.w['Window'], "destroy", "wid", wid
        self.w['Window'].set_property('visible', False)
        return True  # stops further processing...

    def destroy(self):
        self.w['Window'].destroy()

    def add(self, wdg, ev, field, after=None, show=True):
        """this adds a field to the filter panel + operator and string entry
        after: entry will be positioned after widget 'after'
        """
        attrs = dir(ev)
#         for i in attrs:
#             print i, getattr(ev, i)
        field_name_event_box = gtk.EventBox()
        field_name = gtk.Label(field)
        field_name_event_box.add(field_name)
        field_name.set_property('xalign', 0)
        field_name_event_box.connect('button-press-event', self.pop_menu,
                                     'show=True')
                                     


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

    def pop_menu(self, wdg, ev):
        #print "pop_menu", wdg, ev
        self.w['M=opts'].popup(None, None, None, ev.button, ev.time )

        
    def sql(self):
        """create a sql statement composing all requests
        returns a sql whereclause and a bindparam dictionary
        """
        ret = []
        values={}
        for fld in self.fields:
            value = fld['entry'].get_text()
            if len(value) > 0:
                operator = fld['operator'].get_active_text()
                if operator in ('IS NULL', 'IS NOT NULL'):
                    ret += [ "%s %s" %(fld['field'], operator) ]
                else:
                    values[fld['field']] = value
                    ret += [ "%s %s :%s"% (fld['field'],
                                           operator, fld['field'] ) ]
        #print " AND ".join(ret), str(values)
        return (" AND ".join(ret), values)
