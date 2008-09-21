# SqlTreeView.py -- Class for viewing sqldata in a TreeView.
#
#
# Copyright (C) 2005-2006, Michele Comitini <mcm@glisco.it>
# Copyright (C) 2005-2008, Sandro Dentella <sandro@e-den.it>
# 
"""
SqlTable: a widget to edit sql in table mode

a model (self.listore) holds one single instance of the class is linked with the
mapper. column.set_cell_data_func on each column will set the value from there.

A second dummy instance will be used by method self.record_changed to tell if a
record needs saving. So each rendered, when exiting from 'edited' signal needs to
save both in the object *and* in this dummy class.

This is necessary since it is difficoult to understand when an instance has been
changed in presence of an added default. record_changed() will tell if the record
has been changed based on the dummy instance

"""


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
import sqlkit
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
        self.setup_field_validation()
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

        
        menu = self.w['M=popup'] = gtk.Menu()

        ## add to filter
        item = gtk.MenuItem(label="add %s to filter" % field_name.replace('_', ' '))
#        item.connect('activate', self.filter_panel.add, ev, field_name )
        item.connect('activate', self.filter_panel.add, ev, field_name, self )
        menu.append(item)

        ## sort
        if not self.relationship_leader:
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
        
    
    def setup_field_validation(self):
        from sqlkit.widgets.common.fields import FieldChooser
        field_chooser = FieldChooser(self)
        self.vfields = {}
        for field_name in self.field_list:
            ## vfield as validation...
            
            self.vfields[field_name] = field_chooser.get_field(field_name,
                                                              self.fields[field_name])
            
        
    def setup_treeview_columns(self):
        """Setup the presentation of columns.
        Some assumptions are made:
        - bool render to toggles
        - other render to editable text cells
        """

        #create and append columns
        self.tvcolumns = {}
        for i,field_name in enumerate(self.field_list):
            j = i+1
            if field_name in widgets.info:
                v_txt = widgets.info[field_name][0]
            else:
                v_txt = field_name
            #dbg.write("i=%s - j=%s v=%s" % (i, j, v))
            tvcolumn = gtk.TreeViewColumn(v_txt.replace('_',' '))
            ptype = self.fields[field_name]['type']

            #boolean -> checkbox
            if ptype == bool:
                cell = gtk.CellRendererToggle()
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'active', j )
                cell.set_property('activatable', True)
                cell.connect('editing-started', self.generic_editing_started_cb, field_name )

                if self.is_nullable(field_name):
                    cell.connect('toggled', self.toggled_null_signal_cb,
                                 (self.liststore, field_name))
                else:
                    cell.connect('toggled', self.toggled_signal_cb,
                                 (self.liststore, field_name))
                tvcolumn.set_cell_data_func(cell, self.cell_bool_cb, field_name)
                
            ## Dates
            elif self.is_date(field_name):
                #dbg.write('%s is a date' % field_name)
                cell = CellRendererDate()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'date', j )
                cell.connect('editing-started', self.generic_editing_started_cb, field_name )
                cell.connect('date-changed', self.date_changed_cb, field_name )
                tvcolumn.set_cell_data_func(cell, self.cell_default_cb, ('date', field_name) )
                                            

            ## Datetime
            elif self.is_datetime(field_name):
                #dbg.write('%s is a date' % field_name)
                cell = CellRendererDatetime()
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.set_property('sensitive', False)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'datetime', j )
                cell.connect('editing-started', self.generic_editing_started_cb, field_name )
                cell.connect('datetime-changed', self.date_changed_cb, field_name )
                tvcolumn.set_cell_data_func(cell, self.cell_default_cb,('datetime', field_name) )
                                            

            elif self.is_fkey(field_name) :
                # use set_fkey_descr function to put text in the cell
                # if this is a foreign key
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                #cell.set_property('editable-set', True)
                #cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.text_edited_cb, field_name)
                cell.connect('editing-started', self.text_editing_started_cb, field_name)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'text', j)
                tvcolumn.set_cell_data_func(cell, self.set_fkey_descr, field_name)
            else:
                cell = gtk.CellRendererText()
                cell.set_property('editable', True)
                cell.set_property('editable-set', True)
                cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
                cell.connect('edited', self.text_edited_cb, field_name)
                cell.connect('editing-started', self.text_editing_started_cb, field_name)
                tvcolumn.pack_start(cell, True)
                #tvcolumn.add_attribute(cell, 'text', j )
                tvcolumn.set_cell_data_func(cell, self.cell_default_cb, ('text', field_name) )

            self.tvcolumns[field_name] = tvcolumn
            event_box = gtk.EventBox()
            label = gtk.Label()
            label.set_markup(field_name)
            event_box.add(label)
            event_box.show_all()
            tvcolumn.set_widget(event_box)

            #tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            tvcolumn.set_resizable(True)
            tvcolumn.set_expand(True)
            if not self.is_nullable(field_name) and not self.fields[field_name]['default']:
                label.set_markup('<b><i>%s</i></b>' % field_name)
                
            if not self.is_editable(field_name):
                #dbg.write('%s not editable' % field_name)
                try:
                    cell.set_property('editable', False)
                except:
                    cell.set_property('sensitive', False)

            ## left alignment for NUMBERS
            if self.fields[field_name]['type'] in sqlwidget.NUMBERS and \
                   not self.is_fkey(field_name) :
                cell.set_property('xalign', 1.0)

            if self.is_fkey(field_name):
                cell.set_property('foreground', 'navyblue')

            ## positioning for string
            if self.fields[field_name]['type'] == str :
                specs = self.fields[field_name]['col_spec']
                if specs:
                    length = re.search('(\d*)', specs).group(1)
                    try:
                        #dbg.write('lung',length)
                        ## if field has less then 3 chars, position it in the middle
                        if int(length) <= 3:
                            dbg.write(field_name, 'in centro', length, int(length))
                            cell.set_property('xalign', 0.5)
                    except:
                        pass
    
            self.treeview.append_column(tvcolumn)
            self.treeview.columns_autosize()
            tvcolumn.set_clickable(True)
            tvcolumn.connect('clicked', self.clicked_cb, field_name)
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
        event =   gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
        event.button = 1
        dbg.write(event)
        self.popup_col_menu(event, field_name)
        
        return True
    
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
    def toggled_null_signal_cb(self, cell, path, (model, name)):
        """callback that cicle into tri-state"""

	self.model_path = path

        obj = self.liststore[path][0]
        status = getattr(obj, name)
        # status may be True/False/None - I want to cicle
        if status == True:
            status = False
        if status == False:
            status = None
        if status == None:
            status = True

        self.vfields[field_name].set_value( status )        
            
        return True
    
    def toggled_signal_cb(self, cell, path, (model, name)):
        """callback that cicle into True/False"""

	self.model_path = path

        obj = self.liststore[path][0]
        status = getattr(obj, name)

        self.vfields[field_name].set_value(not status)
        
#         if status == True:
#             setattr(obj, name, False)
#         if status == False:
#             setattr(obj, name, True)
            
        return True
    
    def generic_editing_started_cb(self, cell, editable, path, field_name):
        self.currently_edited_field_name = field_name
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

        self.vfields[field_name].set_value(new_text)
        return True
    
#### cell_data_func
    def cell_bool_cb(self, column, cell, model, iter, name):
        """function set by set_cell_data_func for nullable boolean"""

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
        
    def set_fkey_descr(self, column, cell, model, iter, field_name):
        """cell_data_function used by column that have fkey
        """

        fkey = getattr(model.get(iter, 0)[0], field_name)
        path = model.get_path(iter)
        value = self.completion.lookup_value(field_name, fkey)
        cell.set_property('text', value)

    def date_changed_cb(self, event, path, date, col):
	self.model_path = path
        
        obj = self.liststore[path][0]
        setattr(obj, col, date)
        return True
    
        

#### model handling & sqlwidget override
    def record_new(self, widget=None, *args):
        """prepare for 
        """
        if self.block:
            dialog = self.message(type='error', title='Save needed',
                        text='Editing blocked until other field saved')
            if self.response == gtk.RESPONSE_OK:
                dialog.destroy()
            return

        self.record_save()

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
        col = self.get_first_editable_col()

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
        
    def record_save_new(self, ev):
        ## the problem here is to prevent changes in the already used record
        raise NotImplementedError
    
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
        If path, is not passed (as when used from completion)
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
        self.set_height_request(self.treeview, n)
        

    def get_first_editable_col(self):
        """
        return the first visible col to position the cursor on
        """
        
        columns = self.treeview.get_columns()
        for field_name in self.field_list:
            if self.tvcolumns[field_name].get_visible() and self.is_editable(field_name):
                return self.tvcolumns[field_name]
        
#### completion

    def get_value(self, field_name, shown=True):
        """return the value of the cell **currently edited***
        The name is possibly misleading due to parallelism with
        mask. 

        shown: compatibility with mask version
        """
        return self.editable.get_text()





