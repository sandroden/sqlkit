# Copyright (C) 2005-2006, Michele Comitini <mcm@glisco.it>
# Copyright (C) 2005-2006-2007-2008, Sandro Dentella <sandro@e-den.it>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
SqlTable: a widget to edit sql in table mode

a model (self.listore) holds one single instance of the class is linked with the
mapper. column.set_cell_data_func on each column will set the value from there.

"""


import sys
from datetime import datetime
from sqlkit import exc
import sqlalchemy
from sqlkit import debug as dbg
from sqlkit.layout import widgets 
import re
import gobject
import gtk
import sqlkit
from utils import set_height_request, set_all_nonfilling, set_this_filling
from  cell_renderers import CellRendererDate, CellRendererDatetime
import totals
from sqlkit.widgets.common import sqlwidget

class SqlTable(sqlkit.SqlWidget):
    """implementation with a listore with a single column that holds the
    sqlalchemy obj
    """

    __metaclass__ = dbg.LogTheMethods
    edited_row_model_path = None
    currently_edited_field_name = None
    mapper = None
    editable = None
#    commit_allowed = dbg.TraceIt(True, name='commit_allowed', mode='rw')
         
    def __init__(self, *args, **kwargs):
        self.treeview = None
        self.liststore = None
        self.tvcolumns = None
        self.commit_inhibited = False
        self.deleting_row = False
        self.tvcolumns = None
        self.totals = totals.Totals(self)
        sqlkit.SqlWidget.__init__(self, *args, **kwargs)
        
    def _get_layout(self, lay, naked):
        sqlkit.SqlWidget._get_layout(self, lay, naked)
        self.liststore = gtk.ListStore(object)
        ## layout
        self.treeview = self.widgets["TV=tree"]
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
            self.lay_obj.prop('A.external','yscale',1)

#         if self.geom :
#             self.lay_obj.prop('TV=tree', 'width-request', self.geom[0])
#             self.lay_obj.prop('TV=tree', 'height-request', self.geom[1])

        if self.rows:
            self.treeview.connect_after('realize', self.set_rows, self.rows)

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
                self.widgets[b].set_label = None
                self.widgets[b].get_image().set_property('icon-size', 1)
                alignment = self.widgets[b].get_children()[0]
                hbox = alignment.get_children()[0]
                image, label = hbox.get_children()
                label.set_text('')
                

        return (self.lay_obj, self.widgets)


    
    def popup_col_menu(self, ev, field_name):

        try:
            self.widgets['M=popup'].destroy()
        except:
            pass

        
        menu = self.widgets['M=popup'] = gtk.Menu()

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

        ## totals
        if self.get_field_type(field_name) in sqlwidget.NUMBERS and not self.is_fkey(field_name):
            item = gtk.MenuItem(label="create total")
            item.connect('activate', self.add_total_cb, field_name )
            menu.append(item)

        menu.append(gtk.SeparatorMenuItem())
        ## subtotals
        if self.is_date(field_name):
            self.menu_add_date_total_break(menu, field_name)
        else:
            item = gtk.MenuItem(label="subtotal on %s" % (field_name))
            item.connect('activate', self.add_subtotal_cb, field_name )
            menu.append(item)


        menu.show_all()
        menu.popup(None, None, None, ev.button, ev.time)
        #menu.popup(None, None, None, 1, 1)

    def menu_add_date_total_break(self, menu, field_name):

        def add_break_date_cb(menu_item, field_name, period):
            self.totals.add_date_break(field_name, period)

        for period in "day week month quarter year".split():
            item = gtk.MenuItem(label="subtotals on %s" % period)
            item.connect('activate', add_break_date_cb, field_name, period)
            menu.append(item)
        
    def add_total_cb(self, menu_item, field_name):
        self.totals.add_total(field_name)
        
    def add_subtotal_cb(self, menu_item, field_name):
        self.totals.add_break(field_name)

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
        for field_name in self.field_list:
            ## vfield as validation...
            
            self.vfields[field_name] = field_chooser.get_field(field_name,
                                                              self.fields[field_name])
            
        
    def setup_treeview_columns(self):
        """Setup the presentation of columns.
        Some assumptions are made:
        - bool render as toggles
        - other render as editable text cells
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
                tvcolumn.set_cell_data_func(cell, self.cell_dates_cb, ('date', field_name) )
                                            

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
                tvcolumn.set_cell_data_func(cell, self.cell_dates_cb,('datetime', field_name) )
                                            

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
            tvcolumn.set_reorderable(True)

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
            

    def set_field_list(self, field_list):
        """
        Set field of visible columns. Accepts both a list or a string (space or comma separated)
        """
        if isinstance(field_list, (str, unicode)):
            field_list = re.split('[ ,]+', field_list)
        orig_field_list = self.field_list
        for field_name in field_list:
            if field_name in self.fields:
                ## is already known, just make it visible
                self.tvcolumns[field_name].set_property('visible', True)
            else:
                raise NotImplementedError("Column %s is not kown in self.fields" % field_name)
        for field_name in orig_field_list:
            if field_name not in field_list:
                self.tvcolumns[field_name].set_property('visible', False)
        self.field_list = field_list
        
#### callbacks treeview
    def selection_changed_cb(self, treeselection):
        """
        Main callback triggered when the TreeSelection changes. When it happens
        this function tries to record_save()
        """
        # selection change in several different ways:

        # 1. no selection -> selection of existing row
        # 2. no selection -> selection on new row
        # 3. no selection -> reload (does it change?)
        # 4. selected existent record -> reload
        # 5. selected existent record -> other record
        # 6. selected existent record -> new record
        # 7. selected existent record -> delete
        # 8. selected existent LAST record -> delete
        
        if self.edited_row_model_path is None:
            self.record_initialize_vfields()
            self.emit('record_selected')
            return False
        
        ## commit_allowed is a flag that prevents .commit() if a new object
        ## has been created but not yet filled: it wouldn't validate
        if not self.commit_inhibited:
            self.record_save()
            self.record_initialize_vfields()
            self.edited_row_model_path = None

        self.emit('record_selected')
        return False
    
    def record_initialize_vfields(self):
        obj = self.get_current_obj()
        if obj:
            for field_name in self.field_list:
                value = getattr(obj, field_name)
                self.vfields[field_name].set_value(value)
            
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
#         if ksym in dir(self.actions):
#             ret = getattr(self.actions, ksym)(wdg, event, data)
#             dbg.write("RET: ", ret)
#             if ret is True:
#                 return ret
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
            gobject.idle_add(self.treeview.set_cursor, path, columns[0], True)
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

        row = self.get_selected_row() 
        if row is None:
            row = -1
        if row + 1 == len(self.liststore):
            try:
                self.record_new(treeview)
            except exc.CommitError, e:
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
    def toggled_null_signal_cb(self, cell, path, (model, field_name)):
        """callback that cicle into tri-state"""

        self.currently_edited_field_name = field_name
	self.edited_row_model_path = path

        obj = self.liststore[path][0]
        status = getattr(obj, field_name)
        # status may be True/False/None - I want to cicle
        if   status == True:    status = False
        elif status == False:   status = None
        elif status == None:    status = True

        self.vfields[field_name].set_value( status, initial=False )        
            
        return True
    
    def toggled_signal_cb(self, cell, path, (model, field_name)):
        """callback that cicle into True/False"""

	self.edited_row_model_path = path

        obj = self.liststore[path][0]
        status = getattr(obj, field_name)

        self.vfields[field_name].set_value(not status, initial=False)
        
        return True
    
    def generic_editing_started_cb(self, cell, editable, path, field_name):

        self.currently_edited_field_name = field_name
        return True
    
    def text_editing_started_cb(self, cell, editable, path, field_name):

        self.currently_edited_field_name = field_name
        field_type = self.fields[field_name]['type']
        self.editable = editable
        #self.actions.set_entry_connect(self.editable, field_name)
        field_props = self.fields[field_name]

        if hasattr(self.field_widgets[field_name], 'completion'):
            completion = self.field_widgets[field_name].completion
            completion.add_completion(editable)
            completion.add_callbacks(editable)
            
        ## MAX LENGTH
        self.field_widgets[field_name].field.set_max_length()
                
        self.edited_row_model_path = path
        self.commit_inhibited = False
        return True
    
    def text_edited_cb(self, cell, path, new_text, field_name):

        """calback on signal 'edited' on cell_renderer """

        dbg.write(path, new_text, field_name)
        ## NOTE: liststore.clear will trigger text_edited_cb!!!
        if self.deleting_row:
            return True

        if self.edited_row_model_path is None:
            return True

        if self.relationship_mode == 'm2m':
            # in m2m we don't want to edit this field but just to add/remove objects
            # I'm not sure if this should change
            try:
                self.set_current(filter_by={field_name :new_text}, substitute=True)
            except (exc.NoResultFound, exc.MultipleResultsFound), e:
                ## if there's no match, try completion
                show = self.vfields[field_name].widget.completion.show_possible_completion
                show(self.editable, 'start')
                return True
        else:
            self.vfields[field_name].set_value(new_text, initial=False)
        return True
    
#### cell_data_func
    def cell_bool_cb(self, column, cell, model, iter, name):
        """function set by set_cell_data_func for nullable boolean"""

        if not column.get_visible():
            return
        obj = model.get_value(iter, 0) 
        value = getattr(obj, name)
        cell.set_property('active', value)        

        if value is None:
            cell.set_property('inconsistent', True)
        else:    
            cell.set_property('inconsistent', False)
    
    def cell_default_cb(self, column, cell, model, iter, (prop_name, field_name)):
        """function set by set_cell_data_func
        gets the attribute from the record and returns it
        """

        if not column.get_visible():
            return
        obj = model.get_value(iter, 0) 
        value = getattr(obj, field_name)
        cell.set_property(prop_name, value)        
#        cell.set_property('cell-background', None)        
#        cell.set_property('foreground', None)        
        if isinstance(obj, self.totals.total_class):
            obj.set_value_and_colors(cell, value, field_name)
        else:
            cell.set_property('foreground-set', False)
            cell.set_property('cell-background-set', False)
        
    def cell_dates_cb(self, column, cell, model, iter, (prop_name, field_name)):
        """function set by set_cell_data_func
        gets the attribute from the record and returns it
        """
        if not column.get_visible():
            return
        obj = model.get_value(iter, 0) 
        value = getattr(obj, field_name)
        cell.set_property(prop_name, value)        
        
    def set_fkey_descr(self, column, cell, model, iter, field_name):
        """cell_data_function used by column that have fkey
        """
        if not column.get_visible():
            return
        obj = model.get(iter, 0)[0]
        if not obj:
            return
        fkey_value = getattr(obj, field_name)
        if fkey_value:
            path = model.get_path(iter)
            value = self.completions[field_name].lookup_value(field_name, fkey_value)
            cell.set_property('text', value)

    def date_changed_cb(self, event, path, date, col):
	self.edited_row_model_path = path
        
        obj = self.liststore[path][0]
        setattr(obj, col, date)
        return True
    
        

#### model handling & sqlwidget override
    def record_new(self, widget=None, *args):
        """prepare for 
        """

        ## I want to avoid generating a new obj if an object was created 
        ## and not modified (as when you press Down Arrow several times
        ## beyond the lower row)
        if not self.record_has_changed():
            if self.last_new_obj:
                self.sb("Already at new record")
                return
        self.record_save()
        self.treeview.get_toplevel().set_focus(None)

        self.last_new_obj = self.get_new_object()
        # focus the row & start editing

        ## scroll_to_cell will trigger selection_changed_cb
        ## when the new_obj has been added but not yet edited.
        ## we inhibit this 
        #commit_allowed_status = self.commit_allowed
        self.commit_inhibited = True

        treeiter = self.liststore.append([self.last_new_obj])
        path = self.liststore.get_path(treeiter)
        col = self.get_first_editable_col()

        self.treeview.scroll_to_cell(path, col)
        self.treeview.set_cursor(path = path,
                                 focus_column = col,
                                 start_editing = True)
        ## set defaults
        for field_name in self.field_list:
            self.vfields[field_name].set_default()

        self.records += [self.last_new_obj]  ## adding to records is vital to get fk correctly in
                                             ## case this table is a M2M of M2O

        self.commit_inhibited = False

        return True
        
    def record_display(self, index=None):
        """Display all records (appending them to liststore)"""

        if index == None:
            self.liststore.clear()

            for record in self.records:
                self.liststore.append([record])

#        self.emit('record_selected', )
        self.sb("Total N. of records: %s" % (len(self.liststore)))
        
    def record_has_changed(self):
        if self.edited_row_model_path is None:
            return False
        return sqlwidget.SqlWidget.record_has_changed(self)

    def record_save_new(self, ev):
        ## the problem here is to prevent changes in the already used record
        raise NotImplementedError
    
    def record_save(self, ev = None, constraint={}, discard_unchanged=False):

        """save the record

        Detects if any editing has been done consulting self.edited_row_model_path set
        by text_editing_started_cb.

        Detects if INSERT or UPDATE mode by analizing _sqlkit_mode

        see record_validate for constraint explanation

        discard_empty: when record_save is called by reload, an empty record
                       does not need validation

        """

        if self.edited_row_model_path is None: # no editing done
            dbg.write('no self.edited_row_model_path, nothing to save', self.edited_row_model_path)
            return

        obj = self.liststore[self.edited_row_model_path][0]

        if discard_unchanged:
            dbg.write(obj, )
            #if not self.session.is_modified(obj):
            if not self.record_has_changed():
                self.session.expunge(obj)
                del obj
                self.last_new_obj = None
                self.edited_row_model_path = None
                return

        ## if _sqlkit_mode is not set as after a SELECT, it defaults to UPDATE
        ## _sqlkit_mode is set in record_new
    
        mode = getattr(obj, '_sqlkit_mode', 'UPDATE')
            
        ## 
        if not self.record_has_changed():
            self.edited_row_model_path = None
            return

        #rdict.update(self.constraint)
        try:
            self.record_validate(obj, mode, constraint)
        except exc.ValidationError, e:
            self.handle_validate_error(e)
            
        self.commit()
        self.totals.compute()
        self.last_new_obj = None
        
        if hasattr(obj, '_sqlkit_mode'):
            del obj._sqlkit_mode

        ### refresh the data
        #idx = self.sqlData.current
        #self.liststore[self.edited_row_model_path][0] = idx
        #self.edited_row_model_path = None
        #self.record_display(index=idx)

    def unsaved_changes_exist(self):
        """collect possible changes and test if save is needed
        """

        if not self.record_has_changed():
            if self.last_new_obj:
                self.session.expunge(self.last_new_obj)
                del self.last_new_obj
                self.last_new_obj = None
                
        return sqlwidget.SqlWidget.unsaved_changes_exist(self)
        
    def record_delete(self, widget=None, interactive=True):
        """
        Delete a row and corresponding record
        """
        if self.ro:
            return True
        
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

            self.edited_row_model_path = None
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
        self.totals.compute()
        
        self.sb("total N. of records: %s" % len(self.liststore))
        return True
    
    def clear(self, *args, **kwargs):
        self.liststore.clear()
    
    def reload(self, *args, **kwargs):

        try:
            self.record_save(discard_unchanged=True)
        except exc.ValidationError:
            return
        
#        self.session.clear()
        self.commit_inhibited = True
        self.clear()
        ret = sqlwidget.SqlWidget.reload(self, *args, **kwargs)
        self.edited_row_model_path = None
        self.commit_inhibited = False
        self.totals.compute()
        return ret
                                         
    def record_refresh(self):
        """when self.refresh is called other programs have selected the records
        
        """
        self.edited_row_model_path = None  # must be set *before* clear()
                                # to inhibit selection_changed_cp
        self.liststore.clear()
        for i in self.records:
            self.liststore.append([i])
        self.totals.compute()

    def set_value(self, field_name, value, path=None, fkvalue=None, initial=False):
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
            #if value not in (True, False, None):
            if value is not None and not isinstance(value, ptype):
                value = ptype(value)
        except TypeError:
            # eg: setting a field to NULL
            # or: a date that is already in the correct type
            if value is None or type(value) == ptype:
                pass
            else:
                print "problems while handling field: %s value: %s" % (field_name, value)
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
                ## we should not arrive here, but there may be cases I'm missing now...
                raise

        setattr(obj, field_name, value)

        ## text would come up automatically but only after
        ## loosing the focus...
        if fkvalue:
            self.editable.set_text(fkvalue)
        else:
            if value and not self.is_fkey(field_name):
                ## editable, if any, points to the last used editable
                ## that may not be the one that belogs to field_name...
                if self.editable and field_name == self.currently_edited_field_name:
                    self.editable.set_text(str(value))
            
        return True
    
    def get_selected_row(self):
        """Return the path of the selected row or None

        NOTE: treeselection 'changed' signal arrives when the selection changed has
              alreadu occurred

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
        """returns the corrently edited (not just selected!!) obj or obj at path.
        Return None if no selection
        """

        if not path:
            #path = self.get_selected_row()
            path = self.edited_row_model_path

        if path is None:
            return None
        else:
            obj = self.liststore[path][0]
            return obj

    def get_selected_obj(self, path=None):
        """returns the corrently selected obj or obj at path. Return None if no selection"""

        if not path:
            path = self.get_selected_row()

        if path is None:
            return None
        else:
            obj = self.liststore[path][0]
            return obj

    current = property(get_selected_obj)
    def set_current(self, pk=None, substitute=False, filter_by=None):
        """
        retrieve object with primary key pk and set it as current object
        ie: in the row currently selected
        This is mainly used in completion callback for m2m relationship_mode
        """
        
        ## I really need not to flush, since in this moment there is a new object in the
        ## row that started completion that is not ready for flushing
        ## more: it may be due for substitution!!
        
        row = self.get_selected_row()
        obj = self.get_record_no_flush(pk=pk, filter_by=filter_by)
        if substitute:
            expired_obj = self.liststore[row][0]
            self.session.expunge(expired_obj)
            self.records.remove(expired_obj)
            
        self.liststore[row][0] = obj
        self.records += [obj]

    def get_record_no_flush(self, pk=None, filter_by=None):
        """
        Get the record in a way so that no flushing is performed
        """
        query = self.session.query(self.mapper).autoflush(False)
        if pk:
            obj = query.get(pk)
        elif filter_by:
            obj = query.filter_by(**filter_by).one()
        return obj
        
    def set_rows(self, treeview, rows):
        """
        set number of treeview visible rows to "rows"
        """
        dbg.write("setting rows:", rows)
        set_height_request(treeview, rows)




        

    def get_first_editable_col(self):
        """
        return the first visible col to position the cursor on
        """
        
        columns = self.treeview.get_columns()
        second_choice = []
        for field_name in self.field_list:
            if self.tvcolumns[field_name].get_visible() and self.is_editable(field_name):
                if self.vfields[field_name].get_default():
                    second_choice += [self.tvcolumns[field_name]]
                else:
                    return self.tvcolumns[field_name]
        if second_choice:
            return second_choice[0]
           
#### completion

    def get_value(self, field_name, shown=True):
        """return the value of the cell **currently edited***
        The name is possibly misleading due to parallelism with
        mask. 

        shown: compatibility with mask version
        """
        
        if field_name == self.currently_edited_field_name:
            if self.editable:
                return self.editable.get_text()
        return getattr(self.get_current_obj(), field_name)

