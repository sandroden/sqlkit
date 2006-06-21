#!/bin/env python
# SqlTreeView.py -- Class for viewing sqldata in a TreeView.
#
#
# Copyright (C) 2005-2006, Michele Comitini <mcm@glisco.it>
# Copyright (C) 2006, Sandro Dentela <sandro@e-den.it>
# 

import sys
sys.path.append ('../../../')
#from sqlalchemy import *
#import layout
from datetime import datetime
import sqlalchemy.types as sqltypes
import sqlkit.sqlwidget as sqlwidget
#from sqlkit.layoutgenerator import TableLayoutGenerator
import dbg
import decimal

#sys.path.append('../gdl')

if sys.hexversion < 0x20401f0:
    print "your python version: ", hex(sys.hexversion)
    print "needed python version >= ", hex(0x20401f0)
    sys.exit(-1)
    
import gtk, gobject, pango


class CellEditableCalendar(gtk.TextView, gtk.CellEditable):
    date = None
    def __init__(self, date, pos=None, wdg=None, cell_area=None):

        self.date = date
        
        gtk.TextView.__init__(self)
        #self.set_has_window(False)
        self.cal = gtk.Calendar()
        #self.cal.show()
        self.cal.select_month(self.date.month - 1, self.date.year)
        self.cal.select_day(self.date.day)
        self.w = gtk.Window(gtk.WINDOW_POPUP)
        #self.set_editable(False)
        self.w.add(self.cal)
        #self.w.connect("delete_event", self.delete_event)
        self.cal.connect("day-selected-double-click", self.delete_event)
        self.cal.connect("event", self.cal_event)
        self.position_popup(wdg, self.w, cell_area)
        self.show_all()
        self.grab_focus()
        self.w.show_all()
        self.connect('key-press-event', self.keypress_event)
        
    def position_popup(self, widget, popup, ca):
        # the get_origin method returns  the origin comprising the headers
        # the get_cell _area don't!!! (so I add cell_height doing 2*...))

        # you need child to show_all() to get the dimentions correctly
        child = popup.get_children()[0]
        child.show_all()

        popup_width, popup_height = popup.size_request()
        x, y = gtk.gdk.Window.get_origin(widget.window)

        # path, col, x1, y1 = widget.get_path_at_pos(event.x, event.y)
        # ca = widget.get_cell_area(path, col)

        X = x + ca.x
        Y = y + ca.y + 2*ca.height + 4

        # border case: the cell is too close to the border to allow the window
        # I don't want the mouse to be over the popup since an undesired click
        # would change the date...
        if Y + popup_height> gtk.gdk.screen_height():
            Y = y +  ca.y + ca.height - popup_height 
        if X + popup_width> gtk.gdk.screen_width():
            X = gtk.gdk.screen_width() - popup_width 

        popup.move(X, Y)


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
        #dbg.write()
        self.date = None

        return gtk.CellRenderer.__gobject_init__(self, *args, **kwargs)
    
    def do_pango_layout(self, widget):
        pc = widget.get_pango_context()
        pl = pango.Layout(pc)
        pl.set_text(self.date_formatter(self.date))
        return pl
    
    def do_get_size(self, widget, cell_area):

        #dbg.show_caller()
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
        #dbg.ddir(cell_area)
        ce = CellEditableCalendar(date = date, cell_area=cell_area, wdg=widget)
#        ce = CellEditableCalendar(date = date, pos=(event.x, event.y))
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
        
        #dbg.write()
        
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


    

class SqlTable(sqlwidget.SqlWidget):
    """ variant with first column to store the index in sqlData"""

    model_path = None
    treeview = None
    liststore = None
    tvcolumns = None
    mc = None
    mapper = None
    rowCommit = True
    deleting_row = False

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
        #callback for selection changes
        treeselection.connect('changed', self.selection_changed_cb)
        self.treeview.connect('cursor-changed', self.cursor_changed_cb)
        self.treeview.connect('select-cursor-row', self.select_cursor_row_cb)
        #register callback to toplevel window
        self.treeview.get_toplevel().connect("delete_event", self.delete_event)
        self.treeview.connect('key-press-event', self.keypress_event)

        self.setupTreeColumns()
        ## let tree use all the available space... 
        if not self.naked:
            self.lay_obj.prop('A.0','yscale',1)

        return (self.lay_obj, self.w)
    
    def popup_col_menu(self, ev, field_name):
        try:
            self.w['M=popup'].destroy()
        except:
            pass

        
   #self.w['M=popup'] = 
        menu = self.w['M=popup'] = gtk.Menu()

        ## add to filter
        item = gtk.MenuItem(label="add %s to filter" % field_name.replace('_', ' '))
        item.connect('activate', self.filter_panel.add, '', field_name )
        menu.append(item)

        ## sort
        item = gtk.MenuItem(label="sort")
#        item.connect('activate', self.show_widget_properties, widget )
        menu.append(item)

        ## hide
        item = gtk.MenuItem(label="hide")
#        item.connect('activate', self.show_widget_packing, widget )
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        #menu.popup(None, None, None, 1, 1)
        
    def mapToListStore(self):
        self.coltypes = [object]
        for v in self.field_list:
            if self.fields[v]['fkey'] and v.endswith('_id'):
                ftype = type(self.completion._lookup_value(v, ''))
            else:
                ftype = self.fields[v]['type']
            if ftype in sqlwidget.NUMBERS:
                ftype = str
            self.coltypes.append(ftype)
            
        coltypes = []
        
        # try to convert types to gobject types
        for tp in self.coltypes:
            if tp in (int, float, decimal.Decimal):
                coltypes.append(str)
            else:
                try:
                    coltypes.append(gobject.type_from_name(gobject.type_name(tp)))
                except TypeError:
                    coltypes.append(object)

        #dbg.write('coltypes', coltypes)
        if self.liststore is None:
            self.liststore = gtk.ListStore(*coltypes)
    
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
        
    
    def setupTreeColumns(self):
        """Setup the presentation of columns.
        Some assumptions are made:
        - bool render to toggles
        - other render to editable text cells"""
        #create and append columns
        for i,v in enumerate(self.field_list):
            j = i+1
            #dbg.write("i=%s - j=%s v=%s" % (i, j, v))
            tvcolumn = gtk.TreeViewColumn(v.replace('_',' '))
            ptype = self.fields[v]['type']

            #boolean -> checkbox
            if ptype == bool:
                cell = gtk.CellRendererToggle()
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'active', j )
                cell.set_property('activatable', True)
                cell.connect('toggled', self.toggled_signal, (self.liststore, j))
            #primary key and integer do not show
            elif ptype == int and self.fields[v]['pkey']:
                #tvcolumn = gtk.TreeViewColumn(v)
                cell = gtk.CellRendererText()
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'text', j )
#                tvcolumn.set_visible(False)
                tvcolumn.set_visible(True)
            elif issubclass(self.fields[v]['pg_type'], (sqltypes.Date, sqltypes.DateTime)):
                #dbg.write('%s is a date' % v)
                cell = CellRendererDate()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'date', j )
                cell.connect('editing-started', self.date_editing_started, j )
                cell.connect('date-changed', self.date_changed, j )
            elif self.fields[v]['fkey'] and v.endswith('_id'):
                # use set_fkey_descr function to put text in the cell if this is a foreign key
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                #cell.set_property('editable-set', True)
                #cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.edited_signal, v)
                cell.connect('editing-started', self.text_editing_started, v)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'text', j)
                tvcolumn.set_cell_data_func(cell, self.set_fkey_descr, i)
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                cell.set_property('editable-set', True)
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.edited_signal, v)
                cell.connect('editing-started', self.text_editing_started, v)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'text', j )


            if not self.fields[v]['edit']:
                #dbg.write('%s not editable' % v)
                cell.set_property('editable', False)
            self.treeview.append_column(tvcolumn)
            tvcolumn.set_clickable(True)
            tvcolumn.connect('clicked', self.clicked_cb, v)

#### callbacks treeview
    def selection_changed_cb(self, treeselection):
        if self.model_path is None:
            return False
        
        if self.rowCommit:
            self.record_save()
            self.commit()
            self.model_path = None
        return False
    
    def select_cursor_row_cb(self, treeview, start_editing, user_data = None):
        return False
    def cursor_changed_cb(self, treeview, user_data = None):
        return False
        
    def clicked_cb(self, treeview, field_name):
        dbg.write(field_name)
        event =   gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
        event.button = 1
        self.popup_col_menu(event, field_name)
        
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
        #dbg.write('ksym', ksym)

        if ksym in dir(self):
            return getattr(self, ksym)(treeview, event)
    
    def key_shift_ISO_Left_Tab(self, treeview, event):
        #dbg.write('Shift_Tab pressed')
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
        return True
    
    def key_Tab(self, treeview, event):
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
        

#### callbacks columns
    def toggled_signal(self, cell, path, user_data):
        liststore, colnum = user_data

	self.model_path = path

        active = not liststore[path][colnum ]


        liststore[path][colnum ] = active
        return True
    
    def date_editing_started(self, cell, editable, path, col):
        return True
    
    def date_changed(self, event, path, date, col):
	self.model_path = path
        
        self.liststore[path][col] = date
        return True
    
    def edited_signal(self, cell, path, new_text, field_name):
        """called by connect 'edited' on cell_renderer """

        if self.deleting_row:
            return True

        if self.fields[field_name]['fkey']:
            return True
        
        if self.model_path is None:
            return True

        self.set_value(field_name, new_text, path)
    
    def text_editing_started(self, cell, editable, path, field_name):
        #field_type = self.coltypes[col+1]
        field_type = self.fields[field_name]['type']
        #field_name = self.field_list[col]
        field_props = self.fields[field_name]
        if field_type == str or field_props['fkey']:
            #dbg.write("aggiungo <3> per %s type: %s fkey: %s editable: %s" % (
            #    field_name, field_type, field_props['fkey'], editable))
            editable.connect('button-press-event',self.completion.pop_menu,
                           field_name, 3)
            editable.connect('key-press-event',
                             self.completion.entry_short_cut_event,
                             field_name, 'F1')
                
        self.model_path = path
        return True
    

#### model handling & sqlwidget overload
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
        
    def record_display(self):
        self.liststore.clear()
        for i in range(self.sqlData.count()):
            values = self.sqlData.get(i, mode='dict')
            l = [i]
            for k in self.field_list:
                l.append(values[k])
##                 if self.fields[k]['fkey'] and k.endswith('_id'):
##                     l.append(self.completion._lookup_value(k, values[k]))
##                 else:
##                     l.append(values[k])

            #dbg.write(l)
            self.liststore.append(l)
    
        self.sb("Total N. of records: %s" % (len(self.liststore)))
        #sqlwidget.SqlWidget.record_display(new)
        
    def record_save(self, ev = None, constraint={}):
        #rdict = self.path2dict(self.get_idx_of_selected_row())
        rdict = self.path2dict(self.model_path)
        #dbg.write('rdict', rdict)
        if constraint:
            self.constraint=constraint
        #dbg.write('self.constraint', self.constraint)
        rdict.update(self.constraint)
        #dbg.write('RDICT', rdict)
        if not rdict:
            return
        
        if int(self.model_path) > self.sqlData.count() - 1:
            #dbg.write("INSERTING record")
            self.sqlData.add(rdict)
        else:
            #dbg.write("UPDATING record")
            #self.sqlData.set(rdict, index=int(self.model_path))
            self.sqlData.current = self.path2sqldata_index(self.model_path)
            self.sqlData.set(rdict)
        #dbg.write('session', self.session)
        self.session.flush()
        #self.commit()
        
    def record_delete(self, widget=None):
        """Delete a row and corresponding record"""
        #dbg.write('DELETE')
        #self.deleteRow(widget)
        self.deleting_row = True
        def do_del(tm, path, iter):
            """potentially can delete a selection of many rows
            but get_idx_of_selected() supposes that just one row is returned
            """
            self.sqlData.delete(index=self.get_idx_of_selected_row())
            del tm[path]
            self.commit()
            
        sel = self.treeview.get_selection()
        sel.selected_foreach(do_del)
        self.deleting_row = False

        self.sb("total N. of records: %s" % len(self.liststore))
        return True
        
    def reload(self, *args, **kwargs):
        rowCommit = self.rowCommit
        self.rowCommit = None
        self.session.clear()
        ret = sqlwidget.SqlWidget.reload(self, *args, **kwargs)
        self.rowCommit = rowCommit
        #self.set_height_request()

        return ret
                                         
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
    def set_value(self, field_name, value, path=None):
        """ called from within edited signal. Validation should live here"""
        if not path:
            path = self.get_selected_row()
            
        ptype = self.fields[field_name]['type']
        #dbg.write("type", ptype)
        try:
            data = ptype(value)
        except ValueError:
            if value == '' and ptype in (int, float, decimal.Decimal):
                data = value
            else:
                raise
        except TypeError, e:
            #dbg.write( self.coltypes[colnum])
            data = str(value)

        self.liststore[path][self.fname2model_col(field_name)] = data
        return True
    
    def get_selected_row(self):
        sel = self.treeview.get_selection()
        rows = sel.get_selected_rows()[1]
        if rows:
            return rows[0][0]
        else:
            return None
    
    def fname2model_col(self, field_name):
        return self.field_list.index(field_name) + 1
    
    def path2sqldata_index(self, path=None):
        return self.liststore[path][0]
    
    def path2dict(self, path):
        #dbg.write(path)
        #dbg.write(self.liststore[path])
        #dbg.ddir(self.liststore[path])
        rdict = dict(map(None, self.field_list, list(self.liststore[path])[1:]))
        orig = self.sqlData.get(index=self.path2sqldata_index(path))
        for k in rdict.keys():
            ## For numbers we use 'object' column in listore. A '' is really 'none'
            if self.fields[k]['type'] in sqlwidget.NUMBERS:
                if rdict[k] in ('', None):
                    rdict[k] = None
                else:
                    #dbg.write('%s - type: %s' % (k, type(rdict[k])))
                    rdict[k] = self.fields[k]['type'](rdict[k])
                
            ## orig is None for a new row
            if orig is None:
                continue
            
            if not self.fields[k]['edit'] or orig[k] == rdict[k]:
                del rdict[k]
            else:
                pass
                #dbg.write("orig: %s-%s, rdict: %s-%s" % (
                #    (orig[k], type(orig[k]), rdict[k], type(rdict[k]))))
        return rdict
    
    
    def get_idx_of_selected_row(self):
        sel = self.treeview.get_selection()
        model, rows = sel.get_selected_rows()
        row = rows[0]
#         dbg.write('row', row)
#         dbg.write('row', row, 'idx', self.liststore[row])
        if row:
            dbg.write('idx', self.liststore[row][0])
            return self.liststore[row][0]
        else:
            return None
    

#### completion
    def set_fkey_value(self, field_name, value):
        if field_name not in self.field_list:
            #dbg.write('abbandono', field_name)
            return
        
#         if not self.fields[field_name]['fkey']:
#             dbg.write('non foreign key', field_name)
#             return

        #dbg.write(field_name, value, self.model_path)
        try:
            idx = self.field_list.index(field_name)
            #dbg.write(idx)
            self.liststore[self.model_path][idx+1] = value
        except ValueError:
            #dbg.write('Value Error')
            pass
        
        #self.model_path = None
    
    def set_fkey_descr(self, column, cell, tree, iter, i):
        fkey = tree.get(iter, i+1)[0]
        field_name = self.field_list[i]
        #dbg.write(column, i, field_name, fkey)
        cell.set_property('text', self.completion._lookup_value(field_name, fkey))
        

    
    
    
    
    

