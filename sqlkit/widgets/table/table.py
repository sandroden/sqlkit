#!/bin/env python
# SqlTreeView.py -- Class for viewing sqldata in a TreeView.
#
#
# Copyright (C) 2005-2006, Michele Comitini <mcm@glisco.it>
# Copyright (C) 2006, Sandro Dentella <sandro@e-den.it>
# 

import sys
sys.path.append ('../../../')
#from sqlalchemy import *
#import layout
from datetime import datetime
import sqlalchemy.types as sqltypes
from sqlkit.widgets.common import sqlwidget
import sqlalchemy
import dbg
import decimal
import layout.widgets as widgets
import re
import gobject
import gtk
from  cell_renderers import CellRendererDate, CellRendererDatetime
#sys.path.append('../gdl')
NOT_NULL_COLOR = gtk.gdk.color_parse('LightGoldenrod')

if sys.hexversion < 0x20401f0:
    print "your python version: ", hex(sys.hexversion)
    print "needed python version >= ", hex(0x20401f0)
    sys.exit(-1)
    

class SqlTable(sqlwidget.SqlWidget):
    """ variant with first column to store the index in sqlData"""

    model_path = None
    treeview = None
    liststore = None
    tvcolumns = None
    mc = None
    mapper = None
    #rowCommit = dbg.TraceIt(True, name='rowCommit', mode='rw')
    rowCommit = True
    deleting_row = False
    tvcolumns = None
    trace_regexp = 'rowCommit'
#    __metaclass__ = dbg.LogTheMethods
         
    def _get_layout(self, lay, naked):
        sqlwidget.SqlWidget._get_layout(self, lay, naked)
        self.mapToListStore()
        ## layout
        self.treeview = self.w["TV=tree"]
        self.treeview.set_enable_search(False)
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
        self.treeview.connect('key-press-event', self.keypress_event_cb)

        self.setupTreeColumns()
        ## let tree use all the available space... 
        if not self.naked:
            self.lay_obj.prop('A.0','yscale',1)

        if self.geom :
            self.lay_obj.prop('TV=tree', 'width-request', self.geom[0])
            self.lay_obj.prop('TV=tree', 'height-request', self.geom[1])

        if self.icons:
            self.lay_obj.prop(
                ('A.icons', 'xscale', 0),
                ('A.icons', 'xalign', 0),
                ('A.icons', 'left-padding', 0)
                )
            ## just icons, no text
            for b in self.icons.split(" "):
                self.w[b].set_label = None
                self.w[b].get_image().set_property('icon-size', 1)
                alignment = self.w[b].get_children()[0]
                hbox = alignment.get_children()[0]
                image, label = hbox.get_children()
                label.set_text('')
                

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
        item.connect('activate', self.filter_panel.add, ev, field_name )
        menu.append(item)

        ## sort
        item = gtk.MenuItem(label="sort")
        item.connect('activate', self.reload_sort, field_name )
        menu.append(item)

        ## hide
        item = gtk.MenuItem(label="hide")
        item.connect('activate', self.hide_column, field_name )
        menu.append(item)

        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        #menu.popup(None, None, None, 1, 1)
        
    def reload_sort(self, widget, field_name, *args):
        dbg.write(widget, field_name)
        self.order_by = field_name
        self.reload_cb(None)
        
    def reload_cb(self, *args):
        """this is the real callback: C-r and toolbutton 
        """
        dbg.write('pre')
        if hasattr(self, 'filter_panel'):
            self.filter_panel.reload_cb(None)
        else:
            self.reload()
        dbg.write('post')
        
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
                    coltypes.append(
                        gobject.type_from_name(gobject.type_name(tp)))
                except TypeError:
                    coltypes.append(object)

        dbg.write('coltypes', coltypes)
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
        self.tvcolumns = {}
        for i,v in enumerate(self.field_list):
            j = i+1
            if v in widgets.info:
                v_txt = widgets.info[v][0]
            else:
                v_txt = v
            #dbg.write("i=%s - j=%s v=%s" % (i, j, v))
            tvcolumn = gtk.TreeViewColumn(v_txt.replace('_',' '))
            ptype = self.fields[v]['type']

            #boolean -> checkbox
            if ptype == bool:
                cell = gtk.CellRendererToggle()
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'active', j )
                cell.set_property('activatable', True)
                cell.connect('toggled', self.toggled_signal_cb,
                             (self.liststore, j))
                
            # primary key and integer do not show
            elif ptype == int and self.fields[v]['pkey']:
                #tvcolumn = gtk.TreeViewColumn(v)
                cell = gtk.CellRendererText()
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'text', j )
#                tvcolumn.set_visible(False)
                tvcolumn.set_visible(True)

            ## Dates
            elif issubclass(self.fields[v]['db_type'], (sqltypes.Date)):
                #dbg.write('%s is a date' % v)
                cell = CellRendererDate()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', True)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'date', j )
                cell.connect('editing-started', self.date_editing_started_cb, j )
                cell.connect('date-changed', self.date_changed_cb, j )

            ## Datetime
            elif issubclass(self.fields[v]['db_type'], (sqltypes.DateTime)):
                #dbg.write('%s is a date' % v)
                cell = CellRendererDatetime()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'datetime', j )
                cell.connect('editing-started', self.date_editing_started_cb, j )
                cell.connect('datetime-changed', self.date_changed_cb, j )

            elif self.fields[v]['fkey'] and v.endswith('_id'):
                # use set_fkey_descr function to put text in the cell
                # if this is a foreign key
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                #cell.set_property('editable-set', True)
                #cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.text_edited_cb, v)
                cell.connect('editing-started', self.text_editing_started_cb, v)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'text', j)
                tvcolumn.set_cell_data_func(cell, self.set_fkey_descr, i)
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                cell.set_property('editable-set', True)
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.text_edited_cb, v)
                cell.connect('editing-started', self.text_editing_started_cb, v)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, 'text', j )


            self.tvcolumns[v] = tvcolumn
            #tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            tvcolumn.set_resizable(True)
            tvcolumn.set_expand(True)
            if not self.fields[v]['edit']:
                #dbg.write('%s not editable' % v)
                try:
                    cell.set_property('editable', False)
                except:
                    cell.set_property('sensitive', False)

            if self.fields[v]['type'] in sqlwidget.NUMBERS and \
                   not self.fields[v]['fkey'] :
                cell.set_property('xalign', 1.0)

            if self.fields[v]['fkey']:
                cell.set_property('foreground', 'navyblue')

            if self.fields[v]['type'] == str :
                length = re.search('(\d*)', self.fields[v]['col_spec']).group(1)
                try:
                    #dbg.write('lung',length)
                    ## if field has less then 3 char, position it in the middle
                    if int(length) <= 3:
                        dbg.write(v, 'in centro', length, int(length))
                        cell.set_property('xalign', 0.5)
                except:
                    pass

            self.treeview.append_column(tvcolumn)
            self.treeview.columns_autosize()
            tvcolumn.set_clickable(True)
            tvcolumn.connect('clicked', self.clicked_cb, v)
            #tvcolumn.set_fixed_width(self.width)

#### callbacks treeview
    def selection_changed_cb(self, treeselection):
        dbg.write('model_path', self.model_path, 'rowCommit',self.rowCommit)
        if self.model_path is None:
            dbg.write('model_path None, nulla da salvare')
            return False
        
        if self.rowCommit:
            self.record_save()
            #self.commit()
            self.model_path = None
        else:
            pass
            #dbg.write('non self.rowCommit')
            
        return False
    
    def select_cursor_row_cb(self, treeview, start_editing, user_data):
        return False
    
    def cursor_changed_cb(self, treeview, user_data = None):
        return False
        
    def clicked_cb(self, treeview, field_name):
        if self.filter:
            event =   gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
            event.button = 1
            dbg.write(event)
            self.popup_col_menu(event, field_name)
        
            return True
        return False
    
    def hide_column(self, menuItem, field_name,):
        self.tvcolumns[field_name].set_property('visible', False)

#### event handling & accelerators
    def keyrelease_event_cb(self, wdg, event, data=None):
        return self.length_control(wdg, data)
    
    def keypress_event_cb(self, wdg, event, data=None):

        if isinstance(wdg, gtk.TreeView):
            pre = 'tree'
        else:
            #self.length_control(wdg, data)
            pre = 'entry'

        ksym = gtk.gdk.keyval_name(event.keyval)

        mods = ['key_' + pre]
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
        #dbg.write('ksym', ksym, 'mods', mods)
        
        ## precedence to actions
        if ksym in dir(self.actions):
            ret = getattr(self.actions, ksym)(wdg, event, data)
            dbg.write("RET: ", ret)
            if ret == True:
                return ret
        if ksym in dir(self):
            return getattr(self, ksym)(wdg, event, data)
        else:
            self.write_info()
    
    def key_tree_shift_ISO_Left_Tab(self, treeview, event):
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
    
    def key_tree_Tab(self, treeview, event, data):
        path, col = self.treeview.get_cursor()
        ## only visible columns!!
        columns = [c for c in self.treeview.get_columns() if c.get_visible()]
#        dbg.write(columns)
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
        return False
    
    def key_tree_ctrl_n(self, treeview, event, data):
        self.record_new(treeview)
        return False
        
    def key_tree_ctrl_shift_N(self, treeview, event, data):
        dbg.write('OK')
        self.record_new(treeview)
        return False
        
    def key_tree_alt_n(self, treeview, event, data):
        dbg.write('OK')
        self.record_new(treeview)
        return False
        
    def key_tree_ctrl_s(self, treeview, event, data):
        self.record_save(treeview)
        return False
        
    def key_tree_ctrl_k(self, treeview, event, data):
        
        self.record_delete(treeview)
        return False
    
    def key_tree_ctrl_r(self, treeview, event, data):
        self.reload_cb()
        return True
    
    def key_tree_Down(self, treeview, event, data):
        # dbg.write(, len(self.liststore))
        if self.get_selected_row()+1 == len(self.liststore):
            self.record_save()
            self.record_new(treeview)
        return False

        
    def key_entry_shift_Return(self, wdg, event, data):
        self.completion.show_possible_values(wdg, field_name=data, mode='start')
        return True
    
#     def key_tree_Return(self, wdg, event, data):
#         #dbg.write()
#         return False
    
#     def key_entry_Return(self, wdg, event, data):
#         #dbg.write('TEXT',wdg.get_text())
#         return False
    
    def key_entry_F1(self, wdg, event, data):
        self.completion.show_possible_values(wdg, field_name=data, mode='like')
        return True
    
    def key_entry_F2(self, wdg, event, data):
        dbg.write("Eccmi")
        return True
    
    def key_entry_Down(self, wdg, event, data):
        return False
    
    def key_entry_ctrl_Return(self, wdg, event, data):
        self.completion.show_possible_values(wdg, field_name=data, mode='like')
        return True
    
    def length_control(self, wdg, field_name):
        if self.fields[field_name]['type'] is not str:
            return False
        length = self.fields[field_name]['length']
        text = wdg.get_text()
        lstr = len(text)
        if length:
            if lstr > length :
                wdg.set_text(re.sub('.$', '', text))
                self.sb("input exceeded '%s' length (%s)" % (field_name,length))
                return True
        return False

#### callbacks columns
    def toggled_signal_cb(self, cell, path, user_data):
        liststore, colnum = user_data

	self.model_path = path

        active = not liststore[path][colnum ]


        liststore[path][colnum ] = active
        return True
    
    def date_editing_started_cb(self, cell, editable, path, col):
        return True
    
    def date_changed_cb(self, event, path, date, col):
	self.model_path = path
        
        self.liststore[path][col] = date
        return True
    
    def text_editing_started_cb(self, cell, editable, path, field_name):

        field_type = self.fields[field_name]['type']
        self.editable = editable
        self.actions.set_entry_connect(self.editable, field_name)
        field_props = self.fields[field_name]
        if field_type == str or field_props['fkey']:
            editable.connect('button-press-event',self.completion.pop_menu,
                           field_name, 3)
            editable.connect('key-press-event',
                             self.keypress_event_cb, field_name)
            if self.fields[field_name]['type'] is str:
                length = self.fields[field_name]['length']
                if length:
                    editable.set_max_length(length)
#             editable.connect('key-release-event',
#                              self.keyrelease_event_cb, field_name)

                
        self.model_path = path
        dbg.write("self.model_path = %s" % (self.model_path))
        self.rowCommit = True
        return True
    
    def text_edited_cb(self, cell, path, new_text, field_name):

        """called by connect 'edited' on cell_renderer """
        dbg.write(path, new_text, field_name)
        ## NOTE: liststore.clear will trigger text_edited_cb!!!
        if self.deleting_row:
            dbg.write('deleting raw...')
            return True

        if self.model_path is None:
            return True

        self.set_value(field_name, new_text, path)
        return True
    

#### model handling & sqlwidget overload
    def record_new(self, widget=None, *args):
        if self.block:
            dialog = self.message(type='error', title='Save needed',
                        text='Editing blocked until other field saved')
            if self.response == gtk.RESPONSE_OK:
                dialog.destroy()
            return

#        rowCommit = self.rowCommit
#        self.rowCommit = False


        columns = self.treeview.get_columns()

        # get the first visible col to position the cursor on
        for field in self.field_list:
            if self.tvcolumns[field].get_visible() and self.fields[field]['edit']:
                col = self.tvcolumns[field]
                break

        #dbg.write(dir(self.liststore))
        self.treeview.get_toplevel().set_focus(None)
        path = self.liststore.get_path(self.liststore.append())
        self.treeview.scroll_to_cell(path, col)
        self.treeview.set_cursor(path = path,
                                 focus_column = col,
                                 start_editing = True)
#        self.rowCommit = rowCommit
        self.rowCommit = True
        #dbg.write('row_commit', self.rowCommit)
        return True
        
    def record_display(self, index=None):
        if index == None:
            self.liststore.clear()
            indexes = range(self.sqlData.count())
        else:
            #dbg.write('type index', type(index), index)
            indexes = [int(index)]
            
        for i in indexes:
            values = self.sqlData.get(i, mode='dict')
            #dbg.write(values)
            l = [i]
            for k in self.field_list:
                if index is not None:  # refreshing a just inserted row
                    self.liststore[i][self.fname2model_col(k)] = values[k]
                else:
                    l.append(values[k])
            if index == None:
                self.liststore.append(l)
    
        self.sb("Total N. of records: %s" % (len(self.liststore)))
        #sqlwidget.SqlWidget.record_display(new)
        
    def record_save(self, ev = None, constraint={}):

        """save the record. Uses path2dict: see there to understand the value handling

         Detects if any editing has been done consulting self.model_path set
         by text_editing_started_cb.

         Detects if INSERT or UPDATE mode by analizing if the liststore has a
         value in column 0 (should be the index of sqlData)

         constraint: this is a dictionary of values that are enforced. When two
         sqlwidgets are synced is the way the 'master' adds the foreign key
         constraint.

         Constraints are applied *after* path2dict handling and before
         actions.on_update / actions.on_insert

        """

        if self.model_path is None: # no editing done
            return
        
        try:
            index = self.liststore[self.model_path][0]
            mode = 'UPDATE'
            if index is None:
                mode = 'INSERT'
        except IndexError, e:
            dbg.write('Era IndexError')
            mode = 'UPDATE'
            return

            
        rdict = self.path2dict(self.model_path, mode=mode)

        ## 
        if not rdict:
            self.model_path = None
            return

        ## Applying constraint *after* check that I inserted something
        if constraint:
            self.constraint=constraint

        rdict.update(self.constraint)
        
        if mode == 'INSERT':
            self.actions.on_insert(new=rdict)
            dbg.write("INSERTING record", rdict)
            self.sqlData.add(rdict)

        elif mode == 'UPDATE':
            self.actions.on_update(new=rdict, old=self.sqlData.get())
            #self.sqlData.set(rdict, index=int(self.model_path))
            self.sqlData.current = self.path2sqldata_index(self.model_path)
            self.sqlData.set(rdict)

        self.commit()

        ### refresh the data
        idx=self.sqlData.current
        self.liststore[self.model_path][0] = idx
        self.model_path = None
        self.record_display(index=idx)

        
    def record_delete(self, widget=None, interactive=True):
        """Delete a row and corresponding record"""

        if interactive:
            response = self.dialog(type='ok-cancel', text="Delete this record?")
            if response == gtk.RESPONSE_CANCEL:
                return

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
    
    def clear(self, *args, **kwargs):
        self.liststore.clear()
    
    def reload(self, *args, **kwargs):
        rowCommit = self.rowCommit
#        self.rowCommit = None
        #dbg.write('type(session)', type(self.session))
        self.record_save()
        self.session.clear()
        self.clear()
        ret = sqlwidget.SqlWidget.reload(self, *args, **kwargs)
#        self.rowCommit = rowCommit
        self.rowCommit = False
        #self.set_height_request()
        self.model_path = None
        
        self.reloading = False
        return ret
                                         
    def set_value(self, field_name, value, path=None):
        """ called from within edited signal. Validation should live here"""

        #dbg.show_caller(loc=False)
        #dbg.write('field_name:', field_name, 'value:', value)
        if not path:
            path = self.get_selected_row()

        
        ptype = self.fields[field_name]['type']
        #dbg.write("type", ptype)
        try:
            data = ptype(value)
        except ValueError:
            if value == '' and ptype in sqlwidget.NUMBERS:
                data = None
            else:
                raise
        except TypeError, e:
            #dbg.write( self.coltypes[colnum])
            data = str(value)

        self.set_value_real( field_name, data, path)
        
    def set_value_real(self, field_name, value, path):
        idx = self.fname2model_col(field_name)
        #dbg.write("self.liststore[%s][%s] = %s" % (path, idx, data))
        self.liststore[path][idx] = value
        return True
    
    def get_selected_row(self):
        selection = self.treeview.get_selection()
        rows = selection.get_selected_rows()[1]
        if rows:
            return rows[0][0]
        else:
            return None
    
    def fname2model_col(self, field_name):
        return self.field_list.index(field_name) + 1
    
    def path2sqldata_index(self, path=None):
        return self.liststore[path][0]
    
    def path2dict(self, path, mode=None):

        """return a dict from a given path of the listore. Field_name in keys.

        Takes care of a minimal value handling:
           * numbers become None if empty
           * not editable entries are discarded
           * in UPDATE mode only changed values are returned
           * in INSERT mode None and empty values are discarded
           * in INSERT mode False boolean value are discarded (that's the
                       default for checkbox cell)

        """

        rdict = dict(map(None, self.field_list, list(self.liststore[path])[1:]))

        if mode == 'UPDATE':
            index = self.path2sqldata_index(path)
            orig = self.sqlData.get(index=index)
            
        for k in rdict.keys():
            ## For numbers we use 'object' column in listore.
            ## An empty str '' is really 'None'
            if self.fields[k]['type'] in sqlwidget.NUMBERS:
                if rdict[k] in ('', None):
                    rdict[k] = None
                else:
                    rdict[k] = self.fields[k]['type'](rdict[k])
                
            ## let's get rid of key/value NULL or not updated
            if not self.fields[k]['edit']:
                del rdict[k]
                continue
                
            if mode == 'UPDATE' and  orig[k] == rdict[k]:
                del rdict[k]
                continue

            ## when inserting we only pass by NOT NULL values
            if mode == 'INSERT' and k in rdict:
                if rdict[k] is None:
                    del rdict[k]
                elif rdict[k] == '' and self.fields[k]['type'] == str:
                    del rdict[k]
                elif rdict[k] == False and self.fields[k]['type'] == bool:
                    del rdict[k]

        return rdict
    
    
    def get_idx_of_selected_row(self):
        sel = self.treeview.get_selection()
        model, rows = sel.get_selected_rows()
        row = rows[0]
        if row:
            dbg.write('idx', self.liststore[row][0])
            return self.liststore[row][0]
        else:
            return None
    
    def write_info(self):
        path = self.get_selected_row()
        try:
            if self.liststore[path][0] is None:
                self.sb('INSERT mode')
            else:
                self.sb('UPDATE mode')
        except:
            pass  # no selection...
        
    def get_current_record(self):
        """returns a dict of the current selected row"""
        row_n = self.get_selected_row()
        rdict = dict(map(None, self.field_list, list(self.liststore[row_n])[1:]))
        return rdict

#### completion
#     def set_fkey_value(self, field_name, value):

#         #self.set_value(field_name, value)
#         pass

    def set_fkey_descr(self, column, cell, model, iter, i):
        """cell_data_function used by column that have fkey
        """
        #dbg.show_caller(loc=False)
        fkey = model.get(iter, i+1)[0]
        path = model.get_path(iter)
        #dbg.write("FKEY", fkey, path, i+1)
        field_name = self.field_list[i]
        value = self.completion._lookup_value(field_name, fkey)
        #dbg.write(i, field_name, fkey, value)
        cell.set_property('text', value)
        

    
    
    
    
    

