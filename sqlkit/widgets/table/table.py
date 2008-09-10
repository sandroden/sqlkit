#!/bin/env python
# SqlTreeView.py -- Class for viewing sqldata in a TreeView.
#
#
# Copyright (C) 2005-2006, Michele Comitini <mcm@glisco.it>
# Copyright (C) 2005-2008, Sandro Dentella <sandro@e-den.it>
# 

import sys
sys.path.append ('../../../')
#from sqlalchemy import *
#import layout
from datetime import datetime
from sqlkit.widgets.common import sqlwidget, CommitError, ValidationError
import sqlalchemy
import dbg
import decimal
from  layout import widgets 
import re
import gobject
import gtk
from  cell_renderers import CellRendererDate, CellRendererDatetime
#sys.path.append('../gdl')

if sys.hexversion < 0x20401f0:
    print "your python version: ", hex(sys.hexversion)
    print "needed python version >= ", hex(0x20401f0)
    sys.exit(-1)
    

class SqlTable(sqlwidget.SqlWidget):
    """implementation with a listore with a single column that holds the
    sqlalchemy obj
    """

    model_path = None
    treeview = None
    liststore = None
    tvcolumns = None
    mc = None
    mapper = None
    commit_allowed = dbg.TraceIt(True, name='commit_allowed', mode='rw')
    #commit_allowed = True
    deleting_row = False
    tvcolumns = None
#    trace_regexp = 'commit_allowed'
    __metaclass__ = dbg.LogTheMethods
         
    def _get_layout(self, lay, naked):
        sqlwidget.SqlWidget._get_layout(self, lay, naked)
        self.liststore = gtk.ListStore(object)
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
#        self.treeview.connect('select-cursor-row', self.select_cursor_row_cb)
        #register callback to toplevel window
        self.treeview.get_toplevel().connect("delete_event", self.delete_event)
        self.treeview.connect('key-press-event', self.keypress_event_cb)

        self.setup_treeview_columns()
        ## let tree use all the available space... 
        if not self.naked:
            self.lay_obj.prop('A.0','yscale',1)

        if self.geom :
            self.lay_obj.prop('TV=tree', 'width-request', self.geom[0])
            self.lay_obj.prop('TV=tree', 'height-request', self.geom[1])

#         if self.rows:
#             self.set_height_request()

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

        if hasattr(self, 'filter_panel'):
            self.filter_panel.reload_cb(None)
        else:
            self.reload()
    
    def set_height_request(self, rows=None):
        area = self.treeview.get_cell_area(0, self.treeview.get_column(0))

        col      = self.treeview.get_column(0)
        renderer = col.get_cell_renderers()[0]
        spacing  = self.treeview.style_get_property('vertical-separator')

        if not rows:
            rows = len(self.liststore)

            if rows == 0:
                rows = 10
            if rows > 30:
                rows = 30

        # It is not clear where the "+1" pixel comes from, but it's there
        needed_height = (area.height+1) * rows + (spacing) * (rows-1)
        dbg.write('area',area, 'needed', needed_height, 'area.h', area.height)

        # This would not be needed if a previous call to "height-request" hadn't
        # been made. However, there was maybe a reason to do it.
        self.treeview.set_property('height-request', -1)

        toplevel = self.treeview.get_toplevel()
        missing_height = needed_height - self.treeview.get_visible_rect().height

        width  = toplevel.get_allocation().width
        height = toplevel.get_allocation().height 
        toplevel.resize(width, height + missing_height)
        
    
    def setup_treeview_columns(self):
        """Setup the presentation of columns.
        Some assumptions are made:
        - bool render to toggles
        - other render to editable text cells
        """

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
                #tvcolumn.add_attribute(cell, 'active', j )
                cell.set_property('activatable', True)
                cell.connect('toggled', self.toggled_signal_cb,
                             (self.liststore, v))
                tvcolumn.set_cell_data_func(cell, self.cell_bool_cb, v)
                
#             # primary key and integer do not show
#             elif ptype == int and self.fields[v]['pkey']:
#                 #tvcolumn = gtk.TreeViewColumn(v)
#                 cell = gtk.CellRendererText()
#                 tvcolumn.pack_start(cell, True)
#                 #tvcolumn.add_attribute(cell, 'text', j )
# #                tvcolumn.set_visible(False)
#                 tvcolumn.set_visible(True)
#                 tvcolumn.set_cell_data_func(cell, self.cell_fk_text_cb, v)

            ## Dates
            elif self.is_date(v):
                #dbg.write('%s is a date' % v)
                cell = CellRendererDate()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'date', j )
                cell.connect('editing-started', self.date_editing_started_cb, j )
                cell.connect('date-changed', self.date_changed_cb, v )
                tvcolumn.set_cell_data_func(cell, self.cell_default_cb,
                                            ('date', v) )

            ## Datetime
            elif self.is_datetime(v):
                #dbg.write('%s is a date' % v)
                cell = CellRendererDatetime()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'datetime', j )
                cell.connect('editing-started', self.date_editing_started_cb, j )
                cell.connect('datetime-changed', self.date_changed_cb, v )
                tvcolumn.set_cell_data_func(cell, self.cell_default_cb,
                                            ('datetime', v) )

            ### FIXME: only terminating with _id???
            elif self.fields[v]['fkey'] and v.endswith('id'):
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
                tvcolumn.set_cell_data_func(cell, self.set_fkey_descr, v)
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                cell.set_property('editable-set', True)
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.text_edited_cb, v)
                cell.connect('editing-started', self.text_editing_started_cb, v)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'text', j )
                tvcolumn.set_cell_data_func(cell, self.cell_default_cb,
                                            ('text', v) )

            self.tvcolumns[v] = tvcolumn
            event_box = gtk.EventBox()
            label = gtk.Label()
            label.set_markup(v)
            event_box.add(label)
            event_box.show_all()
            tvcolumn.set_widget(event_box)

            #tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            tvcolumn.set_resizable(True)
            tvcolumn.set_expand(True)
            if not self.fields[v]['nullable'] and not self.fields[v]['default']:
                label.set_markup('<b><i>%s</i></b>' % v)
                
            if not self.fields[v]['edit']:
                #dbg.write('%s not editable' % v)
                try:
                    cell.set_property('editable', False)
                except:
                    cell.set_property('sensitive', False)

            ## left alignment for NUMBERS
            if self.fields[v]['type'] in sqlwidget.NUMBERS and \
                   not self.fields[v]['fkey'] :
                cell.set_property('xalign', 1.0)

            if self.fields[v]['fkey']:
                cell.set_property('foreground', 'navyblue')

            ## positioning for string
            if self.fields[v]['type'] == str :
                specs = self.fields[v]['col_spec']
                if specs:
                    length = re.search('(\d*)', specs).group(1)
                    try:
                        #dbg.write('lung',length)
                        ## if field has less then 3 chars, position it in the middle
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
        """
        Main callback triggered when the TreeSelection changes. When it happens
        this function tries to record_save()
        """

        if self.model_path is None:
            return False
        
        ## commit_allowed is a flag that prevents .commit() if a new object
        ## has been created but not yet filled: it wouldn't validate
        if self.commit_allowed:
            self.record_save()
            self.model_path = None
            
        return False
    
    def select_cursor_row_cb(self, treeview, start_editing, user_data):
        return False
    
    def cursor_changed_cb(self, treeview, user_data = None):
        return False
        
    def clicked_cb(self, treeview, field_name):
        if not self.relationship_mode == 'SINGLE':
            return False
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
        
        ## precedence to actions
        if ksym in dir(self.actions):
            ret = getattr(self.actions, ksym)(wdg, event, data)
            dbg.write("RET: ", ret)
            if ret is True:
                return ret
        if ksym in dir(self):
            return getattr(self, ksym)(wdg, event, data)
        else:
            self.write_info()
    
    def key_tree_shift_ISO_Left_Tab(self, treeview, event, data):

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

        self.record_new(treeview)
        return False
        
    def key_tree_alt_n(self, treeview, event, data):

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

        if self.get_selected_row() + 1 == len(self.liststore):
            try:
                self.record_new(treeview)
            except CommitError, e:
                return False

        return False

        
    def key_entry_shift_Return(self, wdg, event, data):
        self.completion.show_possible_completion(wdg, field_name=data, mode='start')
        return True
    
#     def key_tree_Return(self, wdg, event, data):
#         #dbg.write()
#         return False
    
#     def key_entry_Return(self, wdg, event, data):
#         #dbg.write('TEXT',wdg.get_text())
#         return False
    
#     def key_entry_F1(self, wdg, event, data):
#         self.completion.show_possible_completion(wdg, field_name=data, mode='regexp')
#         return True
    
#     def key_entry_F2(self, wdg, event, data):
#         return True
    
# #     def key_entry_Down(self, wdg, event, data):
# #         return 
    
    def key_entry_ctrl_Return(self, wdg, event, data):
        self.completion.show_possible_completion(wdg, field_name=data, mode='like')
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
    def toggled_signal_cb(self, cell, path, (model, name)):
        """callback that cicle into tri-state"""

	self.model_path = path

        obj = self.liststore[path][0]
        status = getattr(obj, name)
        # status may be True/False/None - I want to cicle
        if status == True:
            setattr(obj, name, False)
        if status == False:
            setattr(obj, name, None)
        if status == None:
            setattr(obj, name, True)
            
        return True
    
    def date_editing_started_cb(self, cell, editable, path, col):
        return True
    
    def text_editing_started_cb(self, cell, editable, path, field_name):

        field_type = self.fields[field_name]['type']
        self.editable = editable
        self.actions.set_entry_connect(self.editable, field_name)
        field_props = self.fields[field_name]
        if field_type == str or self.is_fkey(field_name):

            if self.is_fkey(field_name):
                self.completion.add_completion(field_name, 'regex', editable)
            else:
                self.completion.add_simple_completion(field_name, 'regex', editable)

            ## COMPLETION
            editable.connect('button-press-event',self.completion.pop_menu, field_name, 3)
            editable.connect('key-press-event', self.completion.keypress_event_cb, field_name)

            ## MAX LENGTH
            if self.fields[field_name]['type'] is str:
                length = self.fields[field_name]['length']
                if length:
                    editable.set_max_length(length)
#             editable.connect('key-release-event',
#                              self.keyrelease_event_cb, field_name)

                
        self.model_path = path
        dbg.write("self.model_path = %s" % (self.model_path))
        self.commit_allowed = True
        return True
    
    def text_edited_cb(self, cell, path, new_text, field_name):

        """called by connect 'edited' on cell_renderer """

        dbg.write(path, new_text, field_name)
        ## NOTE: liststore.clear will trigger text_edited_cb!!!
        if self.deleting_row:
            return True

        if self.model_path is None:
            return True

        self.set_value(field_name, new_text, path)
        return True
    
    def cell_bool_cb(self, column, cell, model, iter, name):
        """function set by set_cell_data_func for boolean"""

        obj = model.get_value(iter, 0) 
        value = getattr(obj, name)
        cell.set_property('active', value)        

        if value is None:
            cell.set_property('inconsistent', True)
        else:    
            cell.set_property('inconsistent', False)
    
    def cell_default_cb(self, column, cell, model, iter, (prop_name, name)):
        """function set by set_cell_data_func
        gets the attribute from the record and returns it
        """
        obj = model.get_value(iter, 0) 
        value = getattr(obj, name)
        cell.set_property(prop_name, value)        
        
    def cell_fk_text_cb(self, column, cell, model, iter, (col_num, name)):
        """function set by set_cell_data_func for foreign key
        when the field is a fk, we substitute the value with the one found
        in the referred table"""
        ### FIXME: not implemented
        obj = model.get_value(iter, col_num) 
        value = getattr(obj, name)
        cell.set_property("text", value)        
        
    def date_changed_cb(self, event, path, date, col):
	self.model_path = path
        
        obj = self.liststore[path][0]
        setattr(obj, col, date)
        return True
    
        

#### model handling & sqlwidget override
    def record_new(self, widget=None, *args):
        if self.block:
            dialog = self.message(type='error', title='Save needed',
                        text='Editing blocked until other field saved')
            if self.response == gtk.RESPONSE_OK:
                dialog.destroy()
            return

        self.record_save()


        # get the first visible col to position the cursor on
        columns = self.treeview.get_columns()
        for field in self.field_list:
            if self.tvcolumns[field].get_visible() and self.fields[field]['edit']:
                col = self.tvcolumns[field]
                break

        self.treeview.get_toplevel().set_focus(None)

        new_obj = self.get_new_object()
        # focus the row & start editing

        ## scroll_to_cell will trigger selection_changed_cb
        ## when the new_obj has been added but not yet edited.
        ## we inhibit this 
        commit_allowed_status = self.commit_allowed
        self.commit_allowed = False

        treeiter = self.liststore.append([new_obj])
        path = self.liststore.get_path(treeiter)
        self.treeview.scroll_to_cell(path, col)
        self.treeview.set_cursor(path = path,
                                 focus_column = col,
                                 start_editing = True)

        self.commit_allowed = commit_allowed_status

        return True
        
    def record_display(self, index=None):
        """Display all records (appending them to liststore)"""

        if index == None:
            self.liststore.clear()

            for record in self.records:
                self.liststore.append([record])

        self.sb("Total N. of records: %s" % (len(self.liststore)))
        
    def record_save(self, ev = None, constraint={}, discard_empty=False):

        """save the record

        Detects if any editing has been done consulting self.model_path set
        by text_editing_started_cb.

        Detects if INSERT or UPDATE mode by analizing _sqlkit_mode

        see record_validate for constraint explanation

        discard_empty: when record_save is called by reload, an empty record
                       does not need validation

        """

        if self.model_path is None: # no editing done
            dbg.write('no self.model_path, nothing to save', self.model_path)
            return

        obj = self.liststore[self.model_path][0]

        if discard_empty:
            dbg.write(obj, )
            if not self.session.is_modified(obj):
                self.session.expunge(obj)
                del obj
                self.model_path = None
                return

        if obj not in self.records:
            self.records += [obj]  ## adding to records is vital to get fk correctly in
                                   ## case this table is a M2M of M2O

        ## if _sqlkit_mode is not set as after a SELECT, it defaults to UPDATE
        ## _sqlkit_mode is set in record_new
    
        mode = getattr(obj, '_sqlkit_mode', 'UPDATE')
            
        #rdict = self.path2dict(self.model_path, mode=mode)
        rdict = vars(obj)
        ## 
        if not rdict:
            self.model_path = None
            return

        #rdict.update(self.constraint)
        try:
            self.record_validate(obj, mode, constraint)
        except ValidationError, e:
            self.handle_validate_error(e)
            
        self.commit()
        
        if hasattr(obj, '_sqlkit_mode'):
            del obj._sqlkit_mode

        ### refresh the data
        #idx = self.sqlData.current
        #self.liststore[self.model_path][0] = idx
        #self.model_path = None
        #self.record_display(index=idx)

        
    def record_delete(self, widget=None, interactive=True):
        """
        Delete a row and corresponding record
        """

        if interactive:
            response = self.dialog(type='ok-cancel', text="Delete this record?")
            if response == gtk.RESPONSE_CANCEL:
                return

        self.deleting_row = True

        def do_del(model, path, iter):
            """
            potentially can delete a selection of many rows
            """

            obj = model[path][0]
            if obj in self.records:
                self.records.remove(obj)
            if self.relationship_mode == 'SINGLE':
                if obj in self.session.new:
                    self.session.expunge(obj)
                else:
                    self.session.delete(obj)
                #self.session.flush([obj])
                self.commit()
            else:
                pass
                ## we're in M2M relationship or equivalent:
                ## we don't want to delete the object, just delete the relationship
                ## with the referred father
#                self.session.expunge(obj)

#                del obj

            self.model_path = None
            model.remove(iter)
        
        sel = self.treeview.get_selection()
        model, paths = sel.get_selected_rows()
        sel.selected_foreach(do_del)

        ## select the same row or the preceding
        row_n = paths[0][0]  # path is a tuple here
        if row_n >= len(model):
            row_n -= 1

            
        if len(model):  # prevent warning for empty models
            sel.select_path(row_n)
        
        self.deleting_row = False

        self.sb("total N. of records: %s" % len(self.liststore))
        return True
    
    def clear(self, *args, **kwargs):
        self.liststore.clear()
    
    def reload(self, *args, **kwargs):

        try:
            self.record_save(discard_empty=True)
        except ValidationError:
            return
        
        self.session.clear()
        self.commit_allowed = False
        self.clear()
        ret = sqlwidget.SqlWidget.reload(self, *args, **kwargs)
        self.model_path = None
        
        return ret
                                         
    def record_refresh(self):
        """when self.refresh is called other programs have selected the records
        
        """
        self.model_path = None  # must be set *before* clear()
                                # to inhibit selection_changed_cp
        self.liststore.clear()
        for i in self.records:
            self.liststore.append([i])


    def set_value(self, field_name, value, path=None, fkvalue=None):
        """called from within edited signal and completion.
        Validation should live here?
        If path, it not passed (as when used from completion)
        it is deduced from selection
        fkey: if True the value is handled as a primary key. Used from completion
        """

        obj = self.get_current_obj(path=path)

        ## casting of value
        ptype = self.get_field_type(field_name)
        if value == '' and ptype in sqlwidget.NUMBERS:
            value = None

        try:
            value = ptype(value)
        except TypeError:
            if value is None:  #eg: setting a field to NULL 
                pass
            else:
                raise
        except ValueError:
            ## cast may fail becouse you wrote text in a context in which
            ## a fkey is 
            # eg.: you are editing an fk, you wrote text (that is not admitted)
            # just ignore
            # NOTE: you may also have is_fkey = True but with a string key
            #       this case will raise (possibly) a db error on commit

            if self.is_fkey(field_name) and not fkvalue:
                return
            else:
                ## we should not come here, but there may be cases I'm missing now...
                raise

        
        setattr(obj, field_name, value)

        ## text would come up automatically but only after
        ## loosing the focus...
        if fkvalue:
            self.editable.set_text(fkvalue)
        else:
            if value and not self.is_fkey(field_name):
                self.editable.set_text(str(value))
            
        return True
    
    def get_selected_row(self):
        """Return the path of the selected row or None
        """
        selection = self.treeview.get_selection()
        model, rows = selection.get_selected_rows()
        ## we use just the first selected
        #  >>> sel.get_selected_rows()
        #  (<gtk.ListStore object at 0x8dd61bc (GtkListStore at 0x8da6090)>, [(1,)])

        if rows:
            return rows[0][0]
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
        
    def get_current_obj(self, path=None):
        """returns the corrently selected obj or obj at path"""

        if not path:
            path = self.get_selected_row()

        obj = self.liststore[path][0]

        return obj

    def set_current(self, pk=None, substitute=False):
        """
        retrieve object with primary key pk and set it as current object
        ie: in the row currently selected
        This is mainly used in completion callback for m2m relationship_mode
        """

        
        row = self.get_selected_row()
        if substitute:
            self.session.expunge(self.liststore[row][0])
        obj = self.session.query(self.mapper).get(pk)
        self.liststore[row][0] = obj
        self.records += [obj]

    def set_rows(self, n):
        """
        set treeview visible rows to n
        """
        self.set_height_request(n)
        

#### completion

    def set_fkey_descr(self, column, cell, model, iter, field_name):
        """cell_data_function used by column that have fkey
        """
        #dbg.show_caller(loc=False)
        fkey = getattr(model.get(iter, 0)[0], field_name)
        path = model.get_path(iter)
        #dbg.write("FKEY", fkey, path, i+1)
        #field_name = self.field_list[i]
        value = self.completion.lookup_value(field_name, fkey)
        #dbg.write(i, field_name, fkey, value)
        cell.set_property('text', value)

    def get_value(self, field_name, shown=True):
        """return the value of the cell **currently edited***
        The name is possibly misleading due to parallelism with
        mask. 

        shown: compatibility with mask version
        """
        return self.editable.get_text()





