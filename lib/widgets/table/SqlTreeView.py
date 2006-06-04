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
import sqlkit.sqlwidget as sqlwidget
from sqlkit.layoutgenerator import TableLayoutGenerator
import dbg

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
    def __init__(self, date, pos=None, wdg=None):

        self.date = date
        
        gtk.TextView.__init__(self)
        #self.set_has_window(False)
        self.cal = gtk.Calendar()
        self.cal.select_month(self.date.month - 1, self.date.year)
        self.cal.select_day(self.date.day)
        self.w = gtk.Window(gtk.WINDOW_POPUP)
        #toplevel = wdg.get_toplevel()
        #dbg.write(toplevel, self.w)
        #self.w.set_transient_for(toplevel)
        self.w.set_gravity(gtk.gdk.GRAVITY_NORTH_WEST)

        x, y = pos
        self.w.move(int(x)+50, int(y)+120)
        self.set_editable(False)
        #dbg.write( "top level", self.get_toplevel() )
        #self.w.set_transient_for(self)
        self.w.add(self.cal)
        #self.w.connect("delete_event", self.delete_event)
        self.cal.connect("day-selected-double-click", self.delete_event)
        self.cal.connect("event", self.cal_event)
        self.show_all()
        self.grab_focus()
        self.w.show_all()
        self.connect('key-press-event', self.keypress_event)
        
    def keypress_event(self, w, event):
        accelname = gtk.accelerator_name(event.keyval, event.state)
        if accelname == 'Delete':
            self.date = None
            self.emit('editing-done')
            return True
        
        return False
        
    def cal_event(self, w, e):
        text = "%02d/%02d/%d" % (self.cal.get_date()[2],
                             self.cal.get_date()[1] + 1,
                             self.cal.get_date()[0])
        tb = self.get_buffer()
        tb.set_text(text)
        return False
    
    def do_start_editing(self, event):
        pass
    
    def do_remove_widget(self):
        pass
    
    def do_stop_editing(self):
        
        self.w.destroy()
        self.destroy()
    
    def do_editing_done(self):
        self.w.destroy()
        self.destroy()
        pass
    
    def delete_event(self, w = None, e = None):
        self.date=self.cal.get_date()
        self.emit('editing-done')
        self.w.destroy()
        self.destroy()
        return True
    
gobject.type_register(CellEditableCalendar)    

class CellRendererDate(gtk.GenericCellRenderer):
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
        if date is None: return "--/--/--"
        return "%02d/%02d/%d" % (date.day, date.month, date.year)
    
    
    def do_start_editing(self, event, widget, path, background_area, cell_area, flags):

        if self.date is None:
            date = datetime.now()
        else:
            date = self.date
            
#        ce = CellEditableCalendar(date = date, pos=(event.x, event.y), wdg=widget)
        ce = CellEditableCalendar(date = date, pos=(event.x, event.y))
        ce.show()
        ce.grab_focus()
        ce.connect('editing-done', self.editing_done, widget, path)
        
        return ce
    
    def editing_done(self, widget, treeview, path):

        if type(widget.date) is tuple:
            tdate = list(widget.date)
            tdate[1] += 1
            self.date = datetime(*tuple(tdate))
        elif widget.date is None:
            self.date = None
            
        self.stop_editing(True)
        self.emit('date-changed', path, self.date)
        return True
    
    def do_render(self, window, widget, background_area, cell_area, expose_area, flags):

        
        x_offset, y_offset, width, height = self.do_get_size(widget, cell_area)
        pl = self.do_pango_layout(widget)
        widget.get_style().paint_layout(window,
                                        gtk.STATE_NORMAL,
                                        True,
                                        cell_area,
                                        widget,
                                        'foo',
                                        cell_area.x + x_offset,
                                        cell_area.y + y_offset,
                                        pl)
    
    def do_set_property(self, gprop, value):
        setattr(self, gprop.name, value)
        
if gobject.pygtk_version < (2, 8):
    gobject.type_register(CellRendererDate)

class SqlTreeView(object):

    treeview = None
    liststore = None
    tvcolumns = None
    mc = None
    mapper = None
    rowCommit = True
    deleting_row = False
    
    def __init__(self, treeview, MappedClass=None, rowCommit=True, checkClass=None):

        if checkClass is not None:
            checkObj = checkClass(self)
        self.mc = MappedClass
        self.mapper = self.mc.mapper
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
        self._init_accelerators()
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
        for i,v in enumerate(self.mapper.c.keys()):
            tvcolumn = gtk.TreeViewColumn(v.replace('_','__'))

            #boolean -> checkbox
            if isinstance(getattr(self.mapper.c, v).type, sqltypes.Boolean):
                cell = gtk.CellRendererToggle()
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'active', i + 1)
                cell.set_property('activatable', True)
                cell.connect('toggled', self.toggled_signal, (self.liststore, i))
            #primary key and integer do not show
            elif isinstance(getattr(self.mapper.c, v).type, sqltypes.Integer) and getattr(self.mapper.c, v).primary_key:
                tvcolumn = gtk.TreeViewColumn()
                tvcolumn.set_visible(False)
            elif isinstance(getattr(self.mapper.c, v).type, sqltypes.DateTime):
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
            #dbg.write(tvcolumn)
            self.treeview.append_column(tvcolumn)
    
    def _init_accelerators(self):
        """Initializes keyboard accelerators"""

        self.treeview.connect('key-press-event', self.keypress_event)
    
    def keypress_event(self, treeview, event):
        accelname = gtk.accelerator_name(event.keyval, event.state)
        dbg.write( "key ", accelname)
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
            self.commit()
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

        active = not liststore[path][colnum +1 ]


        liststore[path][colnum +1] = active
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
            dbg.write( self.coltypes[colnum + 1])
            data = str(new_text)
	
        liststore[path][colnum + 1] = data
        r = liststore[path][0]
        setattr(r, r.c.keys()[colnum], data)
        dbg.write(r.c.keys()[colnum] + ' ' + str(getattr(r,r.c.keys()[colnum])))
        return True
    
        
    def set_special_attributes(self, column, cell_renderer, tree_model, iter, i):
        pass
    
    def insertRow(self, button):
        dbg.write()
        rowCommit = self.rowCommit
        self.rowCommit = False
        columns = self.treeview.get_columns()
        for col in columns:
            if col.get_visible():
                break

        self.treeview.get_toplevel().set_focus(None)
        self.treeview.scroll_to_cell("0", col)
        self.liststore.prepend()
        # FIXME must use sqldata
        if self.mc is None:
            self.mc = self.mapper.class_
        self.liststore[0][0] = self.mc()
        self.treeview.set_cursor(path = "0",
                                 focus_column = col,
                                 start_editing = True)
        self.rowCommit = rowCommit

        return True
    
    def deleteRow(self, button):
        self.deleting_row = True
        def do_del(tm, path, iter):

            self.sqlData.delete(index=self.get_selected_row())
            del tm[path]
            self.commit()
            
        sel = self.treeview.get_selection()
        sel.selected_foreach(do_del)
        self.deleting_row = False


        return True
    
    def mapToListStore(self):
        # suppose there is at least one record(?)
        colnames = self.mapper.c.keys()
        self.coltypes = [object]
        self.coltypes.extend([type(getattr(self.mapper.select()[0],x)) for x in colnames])
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
        for r in self.mapper.select():
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
        self.commit()
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


class SqlWidgetTreeView(sqlwidget.SqlWidget, SqlTreeView):
    Class = "table"
    mod_path = None

    def _get_layout(self, lay, naked):
        sqlwidget.SqlWidget._get_layout(self, lay, naked)
        self.mapToListStore()
        ## layout
        self.treeview = self.w["TV=tree"]
        self.treeview.show_all()
        #dbg.write(type(self.treeview))
        self.treeview.set_model(self.liststore)
        
        self.treeview.set_rules_hint(True)
        #set selection mode
        treeselection = self.treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_SINGLE)
        self._init_accelerators()
        #callback for selection changes
        treeselection.connect('changed', self.selection_changed_cb)
        self.treeview.connect('cursor-changed', self.cursor_changed_cb)
        self.treeview.connect('select-cursor-row', self.select_cursor_row_cb)
        #register callback to toplevel window
        self.treeview.get_toplevel().connect("delete_event", self.delete_event)
        self.setupTreeColumns()
        if not self.naked:
            self.lay_obj.prop('A.0','yscale',1)
        return (self.lay_obj, self.w)
    
    def record_clear(self, widget=None, *args):
        rowCommit = self.rowCommit
        self.rowCommit = False
        columns = self.treeview.get_columns()
        for col in columns:
            if col.get_visible():
                break

        #dbg.write(dir(self.liststore))
        self.treeview.get_toplevel().set_focus(None)
        path = self.liststore.get_path(self.liststore.append())
        self.treeview.scroll_to_cell(path, col)
        self.treeview.set_cursor(path = path,
                                 focus_column = col,
                                 start_editing = True)
        self.rowCommit = rowCommit

        return True
        
    def record_delete(self, widget=None):
        """Delete a row and corresponding record"""
        self.deleteRow(widget)
        self.sb("total N. of records: %s" % len(self.liststore))
    
    def setupTreeColumns(self):
        #dbg.write(self.fields)

        #create and append columns
        for i,v in enumerate(self.fields.keys()):
            #dbg.write( v['pkey'],v['pg_type'], v['pg_type'] == sqltypes.Integer
            tvcolumn = gtk.TreeViewColumn(v.replace('_','__'))

            #boolean -> checkbox
            #dbg.write(v + ': %s, %s ' % (self.fields[v]['pg_type'], str(self.fields[v]['type'])))
            if self.fields[v]['type'] == bool:
                #dbg.write('bool column')
                cell = gtk.CellRendererToggle()
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'active', i )
                cell.set_property('activatable', True)
                cell.connect('toggled', self.toggled_signal, (self.liststore, i))
            #primary key and integer do not show
            elif (issubclass(self.fields[v]['pg_type'], sqltypes.Integer)) and self.fields[v]['pkey']:
                tvcolumn = gtk.TreeViewColumn()
                tvcolumn.set_visible(False)
            elif issubclass(self.fields[v]['pg_type'], (sqltypes.Date, sqltypes.DateTime)):
                #dbg.write('Date column')
                cell = CellRendererDate()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'date', i )
                cell.connect('editing-started', self.date_editing_started, i)
                cell.connect('date-changed', self.date_changed, i )
            elif self.fields[v]['fkey'] and v.endswith('_id'):
                # use set_fkey_descr function to put text in the cell if this is a foreign key
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                #cell.set_property('editable-set', True)
                #cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.edited_signal, (self.liststore, i))
                cell.connect('editing-started', self.text_editing_started, i)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'text', i)
                tvcolumn.set_cell_data_func(cell, self.set_fkey_descr, i)
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                cell.set_property('editable-set', True)
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.edited_signal, (self.liststore, i))
                cell.connect('editing-started', self.text_editing_started, i)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'text', i )
            #tvcolumn.set_cell_data_func(cell, self.set_special_attributes, i)
            #dbg.write(tvcolumn)
            self.treeview.append_column(tvcolumn)
        
    
    def set_fkey_descr(self, column, cell, tree, iter, i):
        fkey = tree.get(iter, i)[0]
        field_name = self.fields.keys()[i]
        cell.set_property('text', self.completion._lookup_value(field_name, fkey))
        
    def mapToListStore(self):
        self.coltypes = []
        for v in self.fields.keys():
            if self.fields[v]['fkey'] and v.endswith('_id'):
                ftype = type(self.completion._lookup_value(v, ''))
            else:
                ftype = self.fields[v]['type']
            self.coltypes.append(ftype)
            
        coltypes = []
        
        # try to convert types to gobject types
        for tp in self.coltypes:
            try:
                coltypes.append(gobject.type_from_name(gobject.type_name(tp)))
            except TypeError:
                coltypes.append(object)


        if self.liststore is None:
            self.liststore = gtk.ListStore(*coltypes)

    
    def reload(self, *args, **kwargs):
        rowCommit = self.rowCommit
        self.rowCommit = None
        ret = sqlwidget.SqlWidget.reload(self, *args, **kwargs)
        self.rowCommit = rowCommit
        #self.set_height_request()

        return ret
                                         
    def record_display(self):
        self.liststore.clear()
        for i in range(self.sqlData.count()):
            values = self.sqlData.get(i, mode='dict')
            l = []
            for k in self.fields.keys():
                l.append(values[k])
##                 if self.fields[k]['fkey'] and k.endswith('_id'):
##                     l.append(self.completion._lookup_value(k, values[k]))
##                 else:
##                     l.append(values[k])

            self.liststore.append(l)
            #dbg.write(l)
            self.sb("Total N. of records: %s" % (len(self.liststore)))
    
    def edited_signal(self, cell, path, new_text, user_data):
        
        liststore, colnum = user_data


        if self.deleting_row:
            return True


        if self.fields[self.fields.keys()[colnum]]['fkey']:
            return True
        
        if self.mod_path is None:
            return True
        
        try:
            data = self.coltypes[colnum](new_text)
        except TypeError, e:
            dbg.write( self.coltypes[colnum])
            data = str(new_text)

        liststore[path][colnum] = data
        return True
    
    
    def toggled_signal(self, cell, path, user_data):
        liststore, colnum = user_data

	self.mod_path = path

        active = not liststore[path][colnum ]


        liststore[path][colnum ] = active
        return True
    
    def date_changed(self, event, path, date, col):
	self.mod_path = path
        
        self.liststore[path][col] = date
        return True
    
    def set_height_request(self):
        area = self.treeview.get_cell_area(0, self.treeview.get_column(0))
        rows = len(self.liststore)
        if rows == 0:
            rows = 10
        if rows > 30:
            rows = 30
        needed_height = area.height * rows
        dbg.write('area',area, 'needed', needed_height, 'area.h', area.height)
        self.treeview.set_property('height-request', needed_height)
        
    
    def selection_changed_cb(self, treeselection):
        if self.mod_path is None:
            return False
        
        if self.rowCommit:
            self.record_save()
            self.commit()
            self.mod_path = None
        return False
    
    def get_selected_row(self):
        sel = self.treeview.get_selection()
        rows = sel.get_selected_rows()[1]
        if rows:
            return rows[0][0]
        else:
            return None
    
    def record_save(self, ev = None, constraint={}):
        rdict = self.path2dict(self.mod_path)
        dbg.write('rdict', rdict)
        if constraint:
            self.constraint=constraint
        dbg.write('self.constraint', self.constraint)
        rdict.update(self.constraint)
        dbg.write('RDICT', rdict)
        
        if int(self.mod_path) > self.sqlData.count() - 1:
            dbg.write("INSERTING record")
            self.sqlData.add(rdict)
        else:
            dbg.write("UPDATING record")
            self.sqlData.set(rdict, index=int(self.mod_path))
    
    def path2dict(self, path):
        dbg.write(path)
        rdict = dict(map(None, self.fields.keys(),
                 self.liststore[path]))
        for k in rdict.keys():
            if self.fields[k]['pkey']:
                del rdict[k]
        return rdict
    
    def set_value(self, field_name, value):
        if field_name not in self.fields.keys():
            dbg.write('abbandono', field_name)
            return
        
#         if not self.fields[field_name]['fkey']:
#             dbg.write('non foreign key', field_name)
#             return

        dbg.write(field_name, value, self.mod_path)
        try:
            idx = self.fields.keys().index(field_name)
            dbg.write(idx)
            self.liststore[self.mod_path][idx] = value
        except ValueError:
            dbg.write('Value Error')
            pass
        
        #self.mod_path = None
    
    def text_editing_started(self, cell, editable, path, col):
        field_type = self.coltypes[col]
        field_name = self.fields.keys()[col]
        field_props = self.fields[field_name]
        if field_type == str or field_props['fkey']:
                #dbg.write("aggiungo <3> per %s" % (field_name))
                #editable.connect('button-press-event',self.completion.pop_menu,
                #               field_name, 3)
                editable.connect('key-press-event',
                               self.completion.entry_short_cut_event,
                               field_name, 'F1')
                
        self.mod_path = path
        return True
    
#### event handling & accelerators
    def keypress_event(self, treeview, event):
        
        ksym = gtk.gdk.keyval_name(event.keyval)

        mods = ['key']
        for prefix, mask in [('ctrl', gtk.gdk.CONTROL_MASK),
                             ('shift', gtk.gdk.SHIFT_MASK),
                             ('alt', gtk.gdk.MOD1_MASK),
                             ('mod2', gtk.gdk.MOD2_MASK),
                             ('mod3', gtk.gdk.MOD3_MASK),
                             ('mod4', gtk.gdk.MOD4_MASK),
                             ('mod5', gtk.gdk.MOD5_MASK),]:
            if event.state & mask:
                mods.append(prefix)

        ksym = '_'.join(mods + [ksym])
        dbg.write('ksym', ksym)

        if ksym in dir(self):
            return getattr(self, ksym)(treeview, event)
    
    def key_shift_ISO_Left_Tab(self, treeview, event):
        dbg.write('Shift_Tab pressed')
        self.ltab_pressed(treeview)
        return True
    
    def key_Tab(self, treeview, event):
        dbg.write('Tab pressed')
        self.tab_pressed(treeview)
        return True
    
    def key_ctrl_n(self, treeview, event):
        self.record_clear(treeview)
        return False
        
    def key_ctrl_s(self, treeview, event):
        self.record_save(treeview)
        return False
        
    def key_ctrl_k(self, treeview, event):
        self.record_delete(treeview)
        return False
        
    def tab_pressed(self, treeview):
        path, col = self.treeview.get_cursor()
        columns = self.treeview.get_columns()
        colnum = columns.index(col)
        if colnum + 1 < len(columns):
            gobject.idle_add(self.treeview.set_cursor, path, columns[colnum + 1], True)
        else:
            tmodel = self.treeview.get_model()
            titer = tmodel.iter_next(tmodel.get_iter(path))
            if titer is None:
                titer = tmodel.get_iter_first()
            path = tmodel.get_path(titer)
            gobject.idle_add(self.treeview.set_cursor, path, columns[1], True)
        return
    
    def ltab_pressed(self, treeview):
        path, col = self.treeview.get_cursor()
        columns = self.treeview.get_columns()
        colnum = columns.index(col)
        if colnum - 1 >= 0:
            gobject.idle_add(self.treeview.set_cursor, path, columns[colnum - 1], True)
        else:
            path = (path[0] - 1,)
            if path[0] < 0:
                path = (len(treeview.get_model()) - 1,)
            gobject.idle_add(self.treeview.set_cursor, path, columns[-1], True)
        return


    ##

class SqlTable(SqlWidgetTreeView): pass
