#!/bin/env python
# SqlTreeView.py -- Class for viewing sqldata in a TreeView.
#
#
# Copyright (C) 2005-2006, Michele Comitini <mcm@glisco.it>
# 

import sys
sys.path.append ('../../../')
from sqlalchemy import *
from layout import *
from datetime import datetime
import sqlalchemy.types as sqltypes

#sys.path.append('../gdl')

if sys.hexversion < 0x20401f0:
    print "your python version: ", hex(sys.hexversion)
    print "needed python version >= ", hex(0x20401f0)
    sys.exit(-1)
    
import gtk, gobject, pango
#import layout
#from SqlChecker import *


class CellEditableCalendar(gtk.TextView, gtk.CellEditable):
    date = None
    def __init__(self, date):

        self.date = date
        
        gtk.TextView.__init__(self)
        #self.set_has_window(False)
        self.cal = gtk.Calendar()
        self.cal.select_month(self.date.month - 1, self.date.year)
        self.cal.select_day(self.date.day)
        self.w = gtk.Window()
        self.set_editable(False)
        print "top level", self.get_toplevel()
        #self.w.set_transient_for(self.get_toplevel())
        self.w.add(self.cal)
        self.w.connect("delete_event", self.delete_event)
        self.cal.connect("day-selected-double-click", self.delete_event)
        self.cal.connect("event", self.cal_event)
        self.show_all()
        self.grab_focus()
        self.w.show_all()
        
    def cal_event(self, w, e):
        text = "%s/%s/%s" % (self.cal.get_date()[2],
                             self.cal.get_date()[1] + 1,
                             self.cal.get_date()[0])
        tb = self.get_buffer()
        tb.set_text(text)
        return False
    
    def do_start_editing(self, event):
        pass
    
    def do_remove_widget(self):
        pass


    def do_editing_done(self):
        pass

    def delete_event(self, w = None, e = None):
        self.emit('editing-done')
        self.w.destroy()
        self.destroy()
        return True
    
gobject.type_register(CellEditableCalendar)    

class CellRendererDate(gtk.CellRenderer):
    date = None
##     editable = None

    __gproperties__ = {
        'date': (gobject.TYPE_PYOBJECT,
                 'date of cell',
                 'date object contained in cell',
                 gobject.PARAM_READWRITE)
        }

    __gsignals__ = {
        'date-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                         (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
                          )
        }    
    def __init__(self, *args, **kwargs):
        self.date = None

        return gtk.CellRenderer.__gobject_init__(self, *args, **kwargs)

    def do_pango_layout(self, widget):
        pc = widget.get_pango_context()
        pl = pango.Layout(pc)
        pl.set_text(self.date_formatter(self.date))
        return pl

    def do_get_size(self, widget, cell_area):

        
        xpad = self.get_property('xpad')
        ypad = self.get_property('ypad')


        xalign = self.get_property('xalign')
        yalign = self.get_property('yalign')


        layout = self.do_pango_layout(widget)
        width, height = layout.get_pixel_size()


        x_offset = xpad
        y_offset = ypad


        if cell_area:


            x_offset = xalign * (cell_area.width - width)
            x_offset = max(x_offset, xpad)
            x_offset = int(round(x_offset, 0))


            y_offset = yalign * (cell_area.height - height)
            y_offset = max(y_offset, ypad)
            y_offset = int(round(y_offset, 0))


        width  = width  + (xpad * 2)
        height = height + (ypad * 2)


        return x_offset, y_offset, width, height
    
    
    def date_formatter(self, date):
        return "%s/%s/%s" % (date.day, date.month, date.year)
    
    
    def do_start_editing(self, event, widget, path, background_area, cell_area, flags):

        ce = CellEditableCalendar(date = self.date)
        ce.show()
        ce.grab_focus()
        ce.connect('editing-done', self.editing_done, widget, path)
        
        return ce

    def editing_done(self, widget, treeview, path):

        tdate = list(widget.cal.get_date())
        tdate[1] += 1
        self.date = datetime(*tuple(tdate))

        self.stop_editing(False)
        self.emit('date-changed', path, self.date)
        return True

    def do_render(self, window, widget, background_area, cell_area, expose_area, flags):

        
        x_offset, y_offset, width, height = self.do_get_size(widget, cell_area)
        pl = self.do_pango_layout(widget)
        widget.get_style().paint_layout(
            window, gtk.STATE_NORMAL, True, cell_area, widget, 'foo',
            cell_area.x + x_offset, cell_area.y + y_offset, pl
        )

    def do_set_property(self, gprop, value):
        setattr(self, gprop.name, value)
        
gobject.type_register(CellRendererDate)

class SqlTreeView(object):

    treeview = None
    liststore = None
    tvcolumns = None
    mc = None
    rowCommit = True
    deleting_row = False
    
    def __init__(self, treeview, MappedClass, rowCommit=True, checkClass=None):

        if checkClass is not None:
            checkObj = checkClass(self)
        self.mc = MappedClass
        self.rowCommit = rowCommit

        #setup a ListStore
        self.mapToListStore()
        #create the treeview
        self.treeview = treeview
        self.treeview.set_model(self.liststore)
        
        self.treeview.set_rules_hint(True)
        #set selection mode
        treeselection = self.treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_SINGLE)
        self.__init_accelerators()
        #callback for selection changes
        treeselection.connect('changed', self.selection_changed_cb)
        self.treeview.connect('cursor-changed', self.cursor_changed_cb)
        self.treeview.connect('select-cursor-row', self.select_cursor_row_cb)
        #register callback to toplevel window
        self.treeview.get_toplevel().connect("delete_event", self.delete_event)
        self.setupTreeColumns()

    def setupTreeColumns(self):
        """Setup the presentation of columns.
        Some assumptions are made:
        - bool render to toggles
        - other render to editable text cells"""
        #create and append columns
        for i,v in enumerate(self.mc.mapper.c.keys()):
            tvcolumn = gtk.TreeViewColumn(v.replace('_','__'))

            #boolean -> checkbox
            if isinstance(getattr(self.mc.mapper.c, v).type, sqltypes.Boolean):
                cell = gtk.CellRendererToggle()
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'active', i + 1)
                cell.set_property('activatable', True)
                cell.connect('toggled', self.toggled_signal, (self.liststore, i))
            #primary key and integer do not show
            elif isinstance(getattr(self.mc.mapper.c, v).type, sqltypes.Integer) and getattr(self.mc.mapper.c, v).primary_key:
                tvcolumn = gtk.TreeViewColumn()
                tvcolumn.set_visible(False)
            elif isinstance(getattr(self.mc.mapper.c, v).type, sqltypes.DateTime):
                cell = CellRendererDate()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'date', i + 1)
                cell.connect('editing-started', self.date_editing_started, i + 1)
                cell.connect('date-changed', self.date_changed, i + 1)
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                cell.set_property('editable-set', True)
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.edited_signal, (self.liststore, i))
                cell.connect('editing-started', self.text_editing_started, i)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'text', i + 1)

            #tvcolumn.set_cell_data_func(cell, self.set_special_attributes, i)
            self.treeview.append_column(tvcolumn)

    def __init_accelerators(self):
        """Initializes keyboard accelerators"""

        self.treeview.connect('key-press-event', self.keypress_event)

    def tab_pressed(self, treeview):
        path, col = self.treeview.get_cursor()
        columns = self.treeview.get_columns()
        colnum = columns.index(col)
        if colnum + 1 < len(columns):
            gobject.idle_add(self.treeview.set_cursor, path, columns[colnum+1], True)
        else:
            tmodel = self.treeview.get_model()
            titer = tmodel.iter_next(tmodel.get_iter(path))
            if titer is None:
                titer = tmodel.get_iter_first()
            path = tmodel.get_path(titer)
            gobject.idle_add(self.treeview.set_cursor, path, columns[0], True)
        return

    def ltab_pressed(self, treeview):
        path, col = self.treeview.get_cursor()
        columns = self.treeview.get_columns()
        colnum = columns.index(col)
        if colnum - 1 >= 0:
            gobject.idle_add(self.treeview.set_cursor, path, columns[colnum-1], True)
        else:
            path = (path[0] - 1,)
            if path[0] < 0:
                path = (len(treeview.get_model()) - 1,)
            gobject.idle_add(self.treeview.set_cursor, path, columns[-1], True)
        return

    def keypress_event(self, treeview, event):
        accelname = gtk.accelerator_name(event.keyval, event.state)
        print "key ", accelname
        if accelname == 'Tab':
            self.tab_pressed(treeview)
            return True
        elif accelname == '<Shift>ISO_Left_Tab':
            self.ltab_pressed(treeview)
            return True
        return False

    def select_cursor_row_cb(self, treeview, start_editing, user_data = None):
        return False
    
    def cursor_changed_cb(self, treeview, user_data = None):
        return False
        
    def selection_changed_cb(self, treeselection):
        if self.rowCommit:
            objectstore.commit()
        return False

    def text_editing_started(self, cell, editable, path, col):

        completion = editable.get_completion()

        if completion is None:
            completion = gtk.EntryCompletion()
            self.set_completion_model(completion, self.liststore)
            editable.set_completion(completion)
            completion.set_text_column(col + 1)

        return True

    def date_editing_started(self, cell, editable, path, col):
        return True
    
    def date_changed(self, event, path, date, col):
        
        self.liststore[path][col] = date
        r = self.liststore[path][0]
        setattr(r, r.c.keys()[col - 1], date)
        return True


    def toggled_signal(self, cell, path, user_data):
        liststore, colnum = user_data

        active = not liststore[path][colnum + 1]


        liststore[path][colnum + 1] = active
        r = liststore[path][0]
        setattr(r, r.c.keys()[colnum], active)
        return True
   
    
    def edited_signal(self, cell, path, new_text, user_data):
        
        liststore, colnum = user_data
	
        if self.deleting_row:
            return True
        
        try:
            data = self.coltypes[colnum + 1](new_text)
        except TypeError, e:
            print self.coltypes[colnum + 1]
            data = str(new_text)
	
        liststore[path][colnum + 1] = data
        r = liststore[path][0]
        setattr(r, r.c.keys()[colnum], data)
        return True
    
        
    def set_special_attributes(self, column, cell_renderer, tree_model, iter, i):
        pass

    def insertRow(self, button):
        rowCommit = self.rowCommit
        self.rowCommit = False
        columns = self.treeview.get_columns()
        for col in columns:
            if col.get_visible():
                break

        self.treeview.get_toplevel().set_focus(None)
        self.treeview.scroll_to_cell("0", col)
        self.liststore.prepend()
        self.liststore[0][0] = self.mc()
        self.treeview.set_cursor(path = "0",
                                 focus_column = col,
                                 start_editing = True)
        self.rowCommit = rowCommit

        return True

    def deleteRow(self, button):
        self.deleting_row = True
        def do_del(tm, path, iter):

            tm[path][0].delete()
            del tm[path]

        sel = self.treeview.get_selection()
        sel.selected_foreach(do_del)
        self.deleting_row = False


        return True

    def mapToListStore(self):
        # suppose there is at least one record(?)
        colnames = self.mc.mapper.c.keys()
        self.coltypes = [object]
        self.coltypes.extend([type(getattr(self.mc.mapper.select()[0],x)) for x in colnames])
	coltypes = [object]
	# try to convert types to gobject types
	for tp in self.coltypes[1: ]:
            try:
                coltypes.append(gobject.type_from_name(gobject.type_name(tp)))
            except TypeError:
                coltypes.append(object)

        if self.liststore is None:
            self.liststore = gtk.ListStore(*coltypes)
        #fill up
        for r in self.mc.mapper.select():
            values = [getattr(r, x) for x in colnames]
            #prepend r itself
            values.insert(0, r)
            self.liststore.append(values)
    

    def reload(self, w):
        self.rowCommit = False
        objectstore.clear()
        self.liststore.clear()
        self.mapToListStore()
        #self.treeview.set_model(self.liststore)
        self.rowCommit = True
        

    def delete_event(self, treeview, event, data=None):
        objectstore.commit()
        return False

    def set_completion_model(self, completion, model):
        completion.set_model(model)
        

    
class SqlLayoutTreeView(SqlTreeView):

    def __init__(self, MappedClass, checkClass=None):
                ### The layout
        lay = """
          {B m=file m=modifica m=opzioni m=aiuto}
          {O tb=gtk-save tb=gtk-delete tb=gtk-new tb=gtk-quit}
          TVS=tree
        """
        self.l = Layout(lay,opts='s', title="ListStorageView")
        self.w = self.l.show(x=self.delete_event)
        self.window = self.w['Window']
        self.l.menu('m=file',
                    ('gtk-open', self.insertRow,),
                    ('-',None,),
                    ('gtk-quit', self.exit_now)
                    )

        self.w['tb=gtk-delete'].connect('clicked', self.deleteRow)
        self.w['tb=gtk-new'].connect('clicked', self.insertRow)
        self.w['tb=gtk-quit'].connect('clicked', self.exit_now)

        #self.l.connect(
        #    ('tb=gtk-delete', 'clicked', self.deleteRow),
        #    ('tb=gtk-new',    'clicked', self.insertRow),
        #    ('tb=gtk-quit',   'clicked', self.exit_now )
        #    )
        

        treeview = self.w['TV=tree']

        SqlTreeView.__init__(self, treeview, MappedClass,
                             checkClass=checkClass)
        

    def delete_event(self, w, e):
        SqlTreeView.delete_event(self, w, e)
        gtk.main_quit()
        return False

    def exit_now(self, widget):
        self.delete_event(widget, None)
        return True

