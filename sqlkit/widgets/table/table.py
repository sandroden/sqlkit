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
from sqlkit import exc
import sqlalchemy
from sqlkit import debug as dbg, _
from sqlkit.layout import widgets, get_label
import re
import gobject
import gtk
import sqlkit
import utils as tv_utils
import cell_renderers
import totals
from sqlkit.widgets.common import sqlwidget
import gtk
import pango

class SqlTable(sqlwidget.SqlWidget):
    """
    implementation with a listore with a single column that holds the
    sqlalchemy obj
    """
#### Signals
    __gsignals__ = {
        'button-press-event' : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_BOOLEAN,
                                # event, obj, field_name
                           (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_STRING,
                            gobject.TYPE_PYOBJECT),
                           ),
        'context-changed' : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_BOOLEAN,
                                # current (or None)
                           (gobject.TYPE_PYOBJECT,),
                           ),
        }

    __metaclass__ = dbg.LogTheMethods
    currently_edited_field_name = None
    mapper = None
    cell_entry = None
    cell_renderers = None
#    commit_allowed = dbg.TraceIt(True, name='commit_allowed', mode='rw')
#### Init & Layout         
    def __init__(self, *args, **kwargs):

        self.treeview = None
        self.liststore = None
        self.tvcolumns = None
        self.commit_inhibited = False
        self.deleting_row = False
        self.tvcolumns = None
        self.totals = totals.Totals(self)
        #self.edited_row_model_path = dbg.TraceIt(True, name='edited_row_model_path', mode='rw')
        self.edited_row_model_path = None
        sqlwidget.SqlWidget.__init__(self, *args, **kwargs)
        self.run_hook('on_init')
        self._new_record = None
        self._fk_layout_nick = {}
        
    def _get_layout(self, lay, naked):

        sqlwidget.SqlWidget._get_layout(self, lay, naked)
        self.liststore = gtk.ListStore(object)
        ## layout
        self.treeview = self.widgets["TV=tree"]
        self.treeview.set_enable_search(False)
        self.treeview.show_all()
        self.treeview.set_model(self.liststore)
        
        self.treeview.set_rules_hint(True)
        # set selection mode
        treeselection = self.treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_SINGLE)
        # callback for selection changes
        treeselection.connect('changed', self.selection_changed_cb)
        self.treeview.connect('cursor-changed', self.cursor_changed_cb)
        self.treeview.connect('key-press-event', self.keypress_event_cb)
        self.treeview.connect('button-press-event', self.button_press_event_cb)

        self.setup_treeview_columns()
        self.menu.fill_menu_hide_fields()
        ## let tree use all the available space... 
        if not self.naked:
            self.lay_obj.prop('A.external','yscale',1)

        if self.rows:
            gobject.idle_add(self.set_rows)

        self.icon_setup()
        self.treeview.hide()
        self.treeview.show()
        gobject.idle_add(tv_utils.set_optimal_width, self.treeview)
        return (self.lay_obj, self.widgets)

    def icon_setup(self):
        """
        setup icons at the botton of the table if any 'icons' was passed to sqlwidget
        """

        self.lay_obj.prop(
            ('A.icons', 'xscale', 0),
            ('A.icons', 'xalign', 0),
            ('A.icons', 'top-padding', 0),
            ('A.icons', 'bottom-padding', 0),
            ('A.icons', 'left-padding', 0)
            )
        ## just icons, no text
        if self.icons:
            for b in self.icons.split(" "):
                self.widgets[b].set_label = None
                self.widgets[b].get_image().set_property('icon-size', 1)
                ## in windows I can't see it...
                self.widgets[b].get_image().show()
                alignment = self.widgets[b].get_children()[0]
                hbox = alignment.get_children()[0]
                image, label = hbox.get_children()
                label.set_text('')

        
    def on_zoom_fit(self, widget, *args):

        tv_utils.zoom_to_fit(self.treeview, resize=True)

    def setup_field_validation(self):
        from sqlkit.widgets.common.fields import FieldChooser
        field_chooser = FieldChooser(self)
        for field_name in self.field_list:
            ## vfield as validation...
            
            self.gui_fields[field_name] = field_chooser.get_field(field_name,
                                                              self.mapper_info.fields[field_name])
            
    def setup_treeview_columns(self):
        """
        Setup the presentation of columns.
        """
        import columns

        self.tvcolumns = {}
        for field_name in self.field_list:
            
            if field_name in widgets.info:
                label = widgets.info[field_name][0]
            else:
                label = field_name

            ## first check if you have a Custom Renderer
            if self.cell_renderers and field_name in self.cell_renderers:
                col = self.cell_renderers.get(field_name)(field_name, label)

            elif self.is_fkey(field_name) :   ## FKey
                col = columns.FKeyColumn(self, field_name, label)

            elif self.is_boolean(field_name):  ## boolean
                col = columns.BooleanColumn(self, field_name, label)

            elif self.is_date(field_name):   ## Dates
                col = columns.DateColumn(self, field_name, label)

            elif self.is_datetime(field_name):  ## Datetime
                col = columns.DateTimeColumn(self, field_name, label)

            elif self.is_number(field_name):  ## Number
                col = columns.NumericColumn(self, field_name, label)

            elif self.is_text(field_name):  ## Multiline
                col = columns.MultilineColumn(self, field_name, label)

            elif self.is_string(field_name):  ## Varchar
                col = columns.VarcharColumn(self, field_name, label)

            else:
                col = columns.VarcharColumn(self, field_name, label)

            self.tvcolumns[field_name] = col.column
            self.treeview.append_column(col.column)

            if field_name in self.hidden_fields:
                col.column.set_visible(False)
            
        self.menu = columns.ColumnMenuProxy(self)
        self.treeview.columns_autosize()
        self.fix_expandable_columns()

    def fix_expandable_columns(self):
        """
        If no column is expandable, make all columns expandable:
        it's very ugly to see just the last one expand
        """

        fix_it = True
        for key, col in self.tvcolumns.iteritems():
            if col.get_property('expand'):
                fix_it = False

        if fix_it:
            for key, col in self.tvcolumns.iteritems():
                col.set_property('expand', True)
            
            
    def set_rows(self):
        """
        set number of treeview visible rows to "rows"
        """
        dbg.write("setting rows:", self.rows)
        tv_utils.set_height_request(self.treeview, self.rows)

    def hide_fields(self, field_name_list='', force=False, ):
        """
        Hide a column and add the entry in the menu to make it show up again
        field_name_list may be a list or a string (in which case it is split with, and spaces)
        """

        if len(field_name_list) == 0:
            field_name_list = self.hidden_fields

        if isinstance(field_name_list, basestring):
            field_name_list = re.split("[ ,]+", field_name_list)
            self.hidden_fields = field_name_list

        if not self.tvcolumns:
            return

        for field_name in field_name_list:
            self.menu.menu_add_toggle_column(field_name)

    def set_field_list(self, field_list):
        """
        Set field of visible columns. Accepts both a list or a string (space or comma separated)
        """
        from copy import copy

        if isinstance(field_list, (str, unicode)):
            field_list = re.split('[ ,]+', field_list)
        orig_field_list = copy(self.field_list)
        for field_name in field_list:
            if field_name in self.mapper_info.fields:
                ## is already known, just make it visible
                self.tvcolumns[field_name].set_property('visible', True)
            else:
                raise NotImplementedError("Column %s is not kown in self.mapper_info.fields" % field_name)
        for field_name in orig_field_list:
            if field_name not in field_list:
                self.tvcolumns[field_name].set_property('visible', False)
            
        prev = None
        for field_name in field_list:
            self.treeview.move_column_after(self.tvcolumns[field_name], prev)
            prev = self.tvcolumns[field_name]
            
        self.field_list = field_list
        

###### Actions/UiManager
    def prepare_actions(self):
        """
        Prepare action needed by UIManager
        """
        sqlwidget.SqlWidget.prepare_actions(self)

        self.actiongroup_table   = gtk.ActionGroup('Table')

        self.actiongroup_edit.add_actions([
            ('New', gtk.STOCK_NEW,   None, '', None, self.record_new_cb),
            ('Delete', gtk.STOCK_DELETE, None, '', None, self.record_delete),
            ('RecordDelete', gtk.STOCK_DELETE, None, '<Control>k', None, self.record_delete),
            ])

        self.actiongroup_table.add_actions([
            ('Zoom-fit', gtk.STOCK_ZOOM_FIT, None, None, None, self.on_zoom_fit),
            ('ShowColumns', None, _('Show field')),  # menuitem
            ('HideColumns', None, _('Hide field')),  # menuitem
#            ('VisibleColumns', None, None),          # menu
#            ('HiddenColumns', None, None),           # menu
            ('Records', None, 'Records'),
            ('Export', None, _('Export'), None, None, self.export),
            ('MaskView', gtk.STOCK_ZOOM_IN, _('View this record in a Mask'), None, None, self.record_in_mask),
            ('MaskViewFKey', gtk.STOCK_ZOOM_IN, _('View this ForeignKey in a Mask'), None, None, self.fkey_record_in_mask),
            ])

    def prepare_uimanager(self):

        from sqlkit.widgets.common import uidescription
        
        sqlwidget.SqlWidget.prepare_uimanager(self)
        self.ui_manager.insert_action_group(self.actiongroup_table, 0)

        self.ui_manager.add_ui_from_string(uidescription.TABLE_UI)

        self.ui_manager.get_action('/Main/Go/Forward').set_visible(False)
        self.ui_manager.get_action('/Main/Go/Back').set_visible(False)

#### callbacks treeview
    def selection_changed_cb(self, treeselection):
        """
        Main callback triggered when the TreeSelection changes. When run
        this function tries to record_save()
        """
        # selection changes in several different ways:

        # 1. no selection -> selection of existing row
        # 2. no selection -> selection on new row
        # 3. no selection -> reload (does it change?)
        # 4. selected existent record -> reload
        # 5. selected existent record -> other record
        # 6. selected existent record -> new record
        # 7. selected existent record -> delete
        # 8. selected existent LAST record -> delete

        if self.edited_row_model_path is None:
            self.emit('record-selected')
            if self.get_selected_obj() or len(self.records):
                self.emit('context-changed', self.get_selected_obj() or self.records[0])
            return False
        
        ## commit_allowed is a flag that prevents .commit() if a new object
        ## has been created but not yet filled: it wouldn't validate
        if not self.commit_inhibited:
            try:
                if self.relationship_mode == 'm2m' and not self.m2m_editable:
                    ## a new record means a record that has not been substituted by completion
                    ## after completion-match the record is in the session but not in session.new
                    self.record_save(discard_unchanged=False, discard_new=True)
                else:
                    self.record_save(discard_unchanged=True)
                self.edited_row_model_path = None
            except exc.ValidationError, e:
                path = self.edited_row_model_path
                self.edited_row_model_path = None
                self.treeview.get_selection().select_path(path)
                self.edited_row_model_path = path                
                return True

        self.emit('record-selected')
        if self.get_selected_obj() or len(self.records):
            self.emit('context-changed', self.get_selected_obj() or self.records[0])
        return False
    
    def select_cursor_row_cb(self, treeview, start_editing, user_data):
        return False
    
    def cursor_changed_cb(self, treeview, user_data = None):
        return False
        
    def show_column(self, menuItem, field_name,):

        self.menu.menu_add_toggle_column(field_name)
        self.tvcolumns[field_name].set_property('visible', True)

    def button_press_event_cb(self, widget, event):
        """
        Block browsing if last edited cell didn't validate
        """
        if self.cell_entry and not self.cell_entry.is_valid():
            if not self.cell_validate():
                return True

        ## emit button-press-event of the sqlwidget: event, field_name, value
        #  this happens before the selection gets changed so we cannot use get_selected_obj()

        try:
            path, column, x_in_cell, y_in_cell = widget.get_path_at_pos(int(event.x),int(event.y))
            iter = self.liststore.get_iter(path)
            obj = self.liststore.get_value(iter,0)
            if isinstance(obj, self.totals.total_class):
                obj = None
            field_name = column.get_data('field_name')
            self._enforce_first_click_just_selects(path, column, field_name)
        except TypeError, e:
            obj = None
            field_name = None
            
        ## enable/disable menu entries
        action = self.ui_manager.get_action('/TreePopup/MaskView')
        action.set_sensitive(obj and True or False)
            
        action_fk = self.ui_manager.get_action('/TreePopup/MaskViewFKey')
        if field_name and self.is_fkey(field_name):
            action_fk.set_visible(True)
            label = self.get_label(field_name).replace('_', '__')
            action_fk.set_property('label', _("View '%s' in a Mask") % label)
        else:
            action_fk.set_visible(False)
            
        action_delete = self.ui_manager.get_action('/TreePopup/RecordDelete')
        action_delete.set_sensitive(obj and True or False)

        menu = None
        if event.button == 3:
            self._field_name = field_name
            menu = self.ui_manager.get_widget('/TreePopup')
            menu.popup(None, None, None, event.button, event.time)
        
        self.emit('button-press-event', event, obj, field_name, menu )
        
        return False

    def _enforce_first_click_just_selects(self, path, column, field_name):
        """
        if selection has changed with a click on a toggle cell, turn that
        cell into insensitive to prevent changeing the value
        """
        
        ## I want the first click on the table to just change the selection, not the value
        ## the problem is that toggled signal happens *before* change in selection, so that
        ## all normal checks based on selection_changed are not yet at work
        selection = self.treeview.get_selection()
        model, rows = selection.get_selected_rows()
        if rows:
            selected_path = rows[0]
        else:
            selected_path = None

        if not path == selected_path and self.gui_fields[field_name].type == bool:
            if column.get_data('cell').get_property('mode') == gtk.CELL_RENDERER_MODE_ACTIVATABLE:
                column.get_data('cell').set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
                gobject.idle_add(column.get_data('cell').set_property, 'mode', gtk.CELL_RENDERER_MODE_ACTIVATABLE)
        
#### event handling 
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
            #cell = col.get_cell_renderers()[0]
            #cell.emit('edited', path, )
            #self.treeview.set_cursor( path, columns[colnum + 1], True)
            #gobject.idle_add(self.treeview.set_cursor, path, columns[colnum + 1], True)

            next_column = columns[colnum + 1]
            next_field_name = next_column.get_data('field_name')
            gobject.idle_add(self.treeview.set_cursor, path,
                             next_column, self.get_direct_edit(next_field_name) )
        else:
            tmodel = self.treeview.get_model()
            titer = tmodel.iter_next(tmodel.get_iter(path))
            if titer is None:
                titer = tmodel.get_iter_first()
            path = tmodel.get_path(titer)
            
            next_column = columns[0]
            next_field_name = next_column.get_data('field_name')
            gobject.idle_add(self.treeview.set_cursor, path, next_column,
                             self.get_direct_edit(next_field_name) )
        return False
    
    def key_tree_ctrl_n(self, treeview, event, data):
        try:
            self.record_new(treeview)
        except exc.ValidationError:
            return True

        return False
        
    def key_tree_ctrl_shift_N(self, treeview, event, data):

        self.record_new(treeview)
        return False
        
    def key_tree_alt_n(self, treeview, event, data):

        self.record_new(treeview)
        return False
        
    def key_tree_ctrl_s(self, treeview, event, data):
        try:
            self.record_save(treeview)
        except exc.ValidationError:
            pass
        return False
        
    def key_tree_ctrl_k(self, treeview, event, data):
        
        self.record_delete(treeview)
        return False
    
    def key_tree_ctrl_x(self, treeview, event, data):
        
        self.record_delete(treeview)
        return False
    
    def key_tree_ctrl_r(self, treeview, event, data):
        self.reload_cb(treeview)
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
            except exc.ValidationError:
                return True

        return False

    def key_entry_ctrl_n(self, widget, event, data):

        try:
            widget.emit('activate')
        except:
            ## CellTextView does not have activate signal
            pass
        self.record_new()
        return True

    def key_tree_ctrl_s(self, treeview, event, data):
        try:
            self.record_save(treeview)
        except exc.ValidationError:
            pass
        return False
       
    def key_entry_Tab(self, widget, event, data):
        """
        Trigger the validation when moving around the cells
        """
        ksym = gtk.gdk.keyval_name(event.keyval)
        if ksym in ('Tab',):
#             ## FIXME: Down and Return should behave differently if the completion is visible
#             if ksym in ('Down'): # and widget.get_completion().get_property('visible'):
#                 return False

            if self.cell_entry and not self.cell_entry.is_valid():
                if not self.cell_validate():
                    return True

    def get_direct_edit(self, field_name):
        """
        return the next column and if browsing must enter in edit mode
        """
#        from datetime import datetime, date, time, timedelta
        if not self.is_editable(field_name):
            return False

        NO_EDIT = (bool,)

        if not self.mapper_info.fields[field_name]['type'] in NO_EDIT:
            return True
        return False
        
#### callbacks columns
    def editable_keypress_cb(self, widget, event):
        """
        Trigger the validation when moving around the cells
        """
        ksym = gtk.gdk.keyval_name(event.keyval)
        if ksym in ('Tab',):
            if self.cell_entry and not self.cell_entry.is_valid():
                if not self.cell_validate():
                    return True

###### Saving
    def set_value(self, field_name, value, path=None, fkvalue=None, initial=False, shown=False):
        """
        called from within edited signal and completion.
        Validation should live here?
        If path, is not passed (as when used from completion)
        it is deduced from selection
        fkey: if True the value is handled as a primary key.
        Used from completion and from gui_fields/tablewidget
        """
        ## note: self.current cannot be used. We don't want the currently selected obj
        ##       but the one that is to be saved. This operation can be triggered
        ##       by a change in selection in which case self.current already points
        ##       to the new selection
        obj = self.get_current_obj(path=path)
        
        if not obj:
            return
        
        ## casting of value
        if self.is_fkey(field_name):
            value = self.gui_fields[field_name].clean_value(value, input_is_fkey=True)
        else:
            value = self.gui_fields[field_name].clean_value(value)
        setattr(obj, field_name, value)

        ## text would come up automatically but only after
        ## loosing the focus...
        if fkvalue:
            self.cell_entry.entry.set_text(fkvalue)
            self.cell_entry.valid = True
            self.cell_entry.text = fkvalue
            self.fkey_value = fkvalue
        else:
            if value is not None and not self.is_fkey(field_name):
                ## editable, if any, points to the last used editable
                ## that may not be the one that belogs to field_name...
                if self.cell_entry and field_name == self.cell_entry.field_name:
                    #self.cell_entry.entry.set_text(str(value))
                    self.cell_entry.entry.set_text(self.gui_fields[field_name].format_value(value))

        if not initial:
            self.run_hook('on_change_value', value, fkvalue, field_name=field_name)

    def get_value(self, field_name, shown=True):
        """
        return the value of the cell **currently edited***
        The name is possibly misleading due to parallelism with
        mask. 

        shown: compatibility with mask version
        """
        
        obj = self.get_current_obj()
        assert obj is not None, _("no current obj: maybe no record has yet been edited")

        if field_name == self.currently_edited_field_name:
            if self.cell_entry:
                text = self.cell_entry.get_text()
                if self.is_fkey(field_name):
                    if shown:
                    ## we can be here becouse a clean_value triggered it. So don't pass there a
                    ## second time. If you ask for 'shown' I give you shown.
                        return text
                    else:
                        return self.gui_fields[field_name].clean_value(text, input_is_fkey=False)
                else:
                    return self.gui_fields[field_name].clean_value(text)
        return getattr(obj, field_name)

    def record_display(self, index=None, check=False):
        """
        Display all records (appending them to liststore)
        check=False  - not used here but present becouse is used in Mask
        """

        if index == None:
            self.liststore.clear()

            for record in self.records:
                self.liststore.append([record])

        # TIP: status bar message
        self.sb(_("Total N. of records: %s") % (len(self.liststore)), seconds=None)
        
    def record_has_changed(self):
        if self.edited_row_model_path is None:
            return False
        return sqlwidget.SqlWidget.record_has_changed(self)

    def record_save_new(self, ev):
        ## the problem here is to prevent changes in the already used record
        raise NotImplementedError
    
    def record_save(self, discard_unchanged=False, discard_new=False):

        """save the record

        Detects if any editing has been done consulting self.edited_row_model_path set
        by text_editing_started_cb.

        see record_validate for constraint explanation

        discard_empty: when record_save is called by reload, an empty record
                       does not need validation

        """

        if self.edited_row_model_path is None: # no editing done
            dbg.write('no self.edited_row_model_path, nothing to save', self.edited_row_model_path)
            return

        obj = self.get_current_obj()

        if discard_unchanged or (discard_new and obj in self.session.new):
            if not self.record_has_changed():
                self.sb(_('Nothing to save'))
                if obj in self.session.new:
                    self.commit_inhibited = True
                    ## removing the liststore element triggers edited_cb
                    ## so I need to set the path to None to prevent errors
                    path = self.edited_row_model_path
                    self.edited_row_model_path = None
                    self.liststore.remove(self.liststore.get_iter(path))
                    self.commit_inhibited = False
                    self.session.expunge(obj)
                    self.records.remove(obj)
                    self._new_record = False
                del obj
                self.last_new_obj = None
                self.edited_row_model_path = None
                return

        ## if the obj is new, you need to validate it anyhow: it was not changed but didn't start
        ## from a validated point    
        if not self.record_has_changed() and obj not in self.session.new:
            self.edited_row_model_path = None
            return

        self.record_validate(obj)
            
        ## in m2m case we don't want to commit now. We would trigger a commit of the
        ## record represented in the SqlMask that may not yet be validated

        if self.relationship_leader and (
            self.relationship_leader.current in self.session.new):
            # TIP: when saving m2m, we delay till leader record will be saved
            self.sb(_('delaying saving when main record will be saved'))
        else:
            try:
                self.commit()
                self.totals.compute()
            except exc.HandledRollback, e:
                iter = self.liststore.get_iter(self.edited_row_model_path)
                self.edited_row_model_path = None
                self.liststore.remove(iter)
                self.sb(_("Record has NOT been saved"), seconds=100)

        self.last_new_obj = None
        self._new_record = False
        
        if hasattr(obj, '_sqlkit_mode'):
            del obj._sqlkit_mode

    def record_new(self, widget=None, *args):
        """prepare for 
        """

        ## I want to avoid generating a new obj if an object was created 
        ## and not modified (as when you press Down Arrow several times
        ## beyond the lower row)
        if not self.record_has_changed():
            #if self.last_new_obj:
            if (self.current and self.current in self.session.new) or self._new_record:
                self.sb(_("Already at new record"))
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

        #treeiter = self.liststore.append([self.last_new_obj])
        treeiter = self._get_next_iter(self.last_new_obj)
        path = self.liststore.get_path(treeiter)
        col = self.get_first_editable_col()

        self.treeview.scroll_to_cell(path, col)
        self.treeview.set_cursor(path = path,
                                 focus_column = col,
                                 start_editing = True)
        ## set defaults
        for field_name in self.field_list:
            self.gui_fields[field_name].set_default()

        self.records += [self.last_new_obj]  ## adding to records is vital to get fk correctly, in
                                             ## case this table is a M2M of M2O

        self.commit_inhibited = False
        self._new_record = True
        return True

    def unsaved_changes_exist(self, skip_check=False):
        """collect possible changes and test if save is needed
        """

        if not skip_check and not self.record_has_changed():
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
            text = _("Delete this record?\n(%s)") % self.current
            response = self.dialog(type='ok-cancel', text=text)
            if response == gtk.RESPONSE_CANCEL:
                return

        self.deleting_row = True

        def do_del(model, path, iter):
            """
            potentially can delete a selection of many rows
            """

            obj = model[path][0]
            deleted = True
            
            if self.relationship_mode == 'SINGLE':
                if obj in self.session.new:
                    self.session.expunge(obj)
                else:
                    self.session.delete(obj)
                #self.session.flush([obj])
                try:
                    self.commit()
                except exc.HandledRollback, e:
                    deleted = False
                        
            else:
                ## we're in M2M relationship or equivalent:
                ## we don't want to delete the object, just delete the relationship
                ## with the referred father
                if obj in self.session.new:
                    self.session.expunge(obj)

            if deleted:
                self.edited_row_model_path = None
                model.remove(iter)
                if obj in self.records:
                    self.records.remove(obj)
        
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
        
        self.sb(_("Total N. of records: %s") % len(self.liststore), seconds=None)
        return True
    
    def _get_next_iter(self, new_obj):
        """
        get a new iter inserting a row just before last (sub)/total - if any-
        """
        if not len(self.liststore):
            return self.liststore.append([new_obj])

        for i in range(-1, -5, -1):
            obj = self.liststore.get_value( self.liststore[i].iter, 0)
            if isinstance(obj, self.totals.total_class):
                continue
            row = self.liststore[i]
            break

        return self.liststore.insert_after(row.iter, [new_obj])

###### Validation
    def cell_validate(self):
        """
        validate cell value, return True if ok
        The cell to be validated is the last visited cell, ie: the one whose field_name, path and cell
        where set inside text_editing_started_cb
        ForeignKey that do not validate should trigger completion

        This must be called by:
          - Return
          - Tab
          - Button1 on other cell
          - edited callback
        """

        new_text = self.cell_entry.get_text()
        field_name = self.currently_edited_field_name

        if self.relationship_mode == 'm2m' and not self.m2m_editable:
            # in m2m we don't want to edit this field but just to add/remove objects
            # I'm not sure if this should change
            if not new_text:
                return True

            try:
                self.set_current(filter_by={field_name :new_text})
                return 
            except (exc.NoResultFound, exc.MultipleResultsFound), e:
                ## if there's no match, try completion
                dbg.write("No match: try completion")
                show = self.gui_fields[field_name].widget.completion.show_possible_completion
                show(self.cell_entry.entry, 'start')
                return True
            except (sqlalchemy.exceptions.DBAPIError), e:
                self.sb(e.message)
                return True
        else:
            ## 
            if self.is_fkey(field_name):
                if not new_text:
                    self.gui_fields[field_name].set_value(None, initial=False)                    
                    return True
                self.sb(_('Value is not valid, trying completion'))
                show = self.gui_fields[field_name].widget.completion.show_possible_completion
                show(self.cell_entry.entry, 'start', sb=False)
                return False
            else:
                try:
                    self.gui_fields[field_name].set_value(new_text, initial=False)
                    self.cell_entry.valid = True
                    return True
                except exc.ValidationError, e:
                    self.cell_entry.valid = False
                    self.sb(e.message)
                    return False
        
        
    def length_control(self, wdg, field_name):
        if self.mapper_info.fields[field_name]['type'] is not str:
            return False
        length = self.mapper_info.fields[field_name]['length']
        text = wdg.get_text()
        lstr = len(text)
        if length:
            if lstr > length :
                wdg.set_text(re.sub('.$', '', text))
                # TIP: check in input field length %s %s -> field_name length
                self.sb(_("Input exceeded max %s length (%s)") % (field_name,length))
                return True
        return False

    def fkey_is_valid(self, field_name):
        """
        return True if current editable -if exists- has a value that does not need validation
        """
        if self.cell_entry and self.cell_entry.is_valid():
            return True
        return False
    

###### Record browsing 
    def initialize_record_editing(self, path, force=False, obj=None):
        """
        register the path of the editing and initialize all validation fields
        called when entering a new row or when a new record is added in m2m
        """
        # in Masks this is done when set_field is used on record_display
        # here the display is automatic via set_cell_data_func so we have to set
        # initial value when starting editing a record
        
        if not self.edited_row_model_path or force:
            if not obj:
                obj = self.get_selected_obj()
            if obj:
                for field in self.gui_fields:
                    value = getattr(obj, field.field_name)
                    dbg.write("initialize %s" % field.field_name)
                    self.gui_fields[field.field_name].set_value(value, initial=True)

        self.edited_row_model_path = path
        
    def clear(self, *args, **kwargs):
        self.liststore.clear()
    
    def reload_cb(self, widget, *args):
        """
        this is the real callback: C-r and toolbutton 
        """

        self.grab_focus(widget)
        
        if hasattr(self, 'filter_panel'):
            self.filter_panel.reload_cb(None)
        else:
            self.reload()
    
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
        self.cell_entry = None
        self.session.rollback()
        if self.get_selected_obj() or len(self.records):
            self.emit('context-changed', self.get_selected_obj() or self.records[0])

        self._new_record = False
        return ret
                                         
    def record_refresh(self):
        """
        when self.refresh is called other programs have selected the records
        """
        self.edited_row_model_path = None  # must be set *before* clear()
                                # to inhibit selection_changed_cp
        self.liststore.clear()
        for i in self.records:
            self.liststore.append([i])
        self.totals.compute()
        self.treeview.columns_autosize()
        sqlwidget.SqlWidget.record_refresh(self)
        if self.get_selected_obj() or len(self.records):
            self.emit('context-changed', self.get_selected_obj() or self.records[0])
        self._new_record = False

    def record_in_mask(self, widget):
        """
        Open a SqlMask to show self.current.
        Hooks are set on the newly created mask so that validation is retained
        Remember to set any possible configuration of the table in an 'on_init'
        hook so that it will be propagated

        """

        from sqlkit.widgets import SqlMask, SqlTable

        mask = SqlMask(mapper=self.mapper, session=self.session, layout=self.layout,
                       relationship_mode='FIXED', metadata=self.metadata, hooks=self.hooks)
        mask.actiongroup_edit.set_sensitive(self.actiongroup_edit.get_sensitive())
        mask.set_records([self.current])

        ## signals to keep selection in sync 
        def follow_selection(table, obj, mask):
            mask.set_records([obj])

#        handler_id = self.connect('record-selected', follow_selection, mask)
        handler_id = self.connect('context-changed', follow_selection, mask)

        def disconnect(mask, id):
            self.disconnect(id)

        mask.connect('delete-event', disconnect, handler_id)

        self._mask = mask

    def fkey_record_in_mask(self, widget):
        """
        Open a SqlMask to show the fkey of this field

        """
        if not hasattr(self, '_field_name'):
            return

        field_name = self._field_name

        del self._field_name
        
        from sqlkit.widgets import SqlMask, SqlTable

        ftable = self.completions[field_name].table

        mask = SqlMask(table=ftable.name, session=self.session, dbproxy=self.dbproxy, 
                       relationship_mode='FIXED', metadata=self.metadata,
                       layout_nick=self._fk_layout_nick.get(field_name, None),
                       )
        mask.actiongroup_edit.set_sensitive(self.actiongroup_edit.get_sensitive())
        mask.set_records(pk=getattr(self.current, field_name))

        ## signals to keep selection in sync 
        def follow_selection(table, obj, mask):
            if obj and self.current:
                mask.set_records(pk=getattr(self.current, field_name))

#        handler_id = self.connect('record-selected', follow_selection, mask)
        handler_id = self.connect('context-changed', follow_selection, mask)

        def disconnect(mask, id):
            self.disconnect(id)

        mask.connect('delete-event', disconnect, handler_id)

        self._fmask = mask  # just for debug

    def set_fk_layout(self, field_name, layout_nick):
        """
        set a layout_nick to be used for a column
        :param field_name: the field_nme of the column
        :param layout_nick: the nick name of the layout to be used a 'layout_nick'
        """
        self._fk_layout_nick[field_name] = layout_nick
            
###### Misc
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
                self.sb(_('INSERT mode'))
            else:
                self.sb(_('UPDATE mode'))
        except:
            pass  # no selection...
        
    def get_current_obj(self, path=None):
        """
        Returns the corrently edited (not just selected!!) obj or obj at path.
        Selection can already be elsewehre (as in on_selection_change)
        Read comment in set_value
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
            if isinstance(obj, self.totals.total_class):
                return None
            return obj

    current = property(get_selected_obj)
    def set_current(self, pk=None, filter_by=None):
        """
        retrieve object with primary key pk and set it as current object
        ie: in the row currently selected
        This is mainly used in completion callback for m2m relationship_mode
        """
        
        ## I really need not to flush, since in this moment there is a new object in the
        ## row that started completion that is not ready for flushing
        ## more: it may be due for substitution!!

        row = self.get_selected_row()
        assert row is not None
        
        obj = self.get_record_no_flush(pk=pk, filter_by=filter_by)

        expired_obj = self.liststore[row][0]
        if expired_obj in self.session:
            self.session.expunge(expired_obj)
        self.records.remove(expired_obj)

        ## assigning liststore value will trigger 'editing-canceled'
        self.cell_entry.substitute = True
        self.cell_entry.valid = True
        self.liststore[row][0] = obj
        
        path = self.edited_row_model_path
        self.initialize_record_editing(path, force=True, obj=obj)

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
        
    def get_first_editable_col(self):
        """
        return the first visible col to position the cursor on
        """
        
        columns = self.treeview.get_columns()
        second_choice = []
        for field_name in self.field_list:
            if self.tvcolumns[field_name].get_visible() and self.is_editable(field_name):
                if self.gui_fields[field_name].get_default():
                    second_choice += [self.tvcolumns[field_name]]
                else:
                    return self.tvcolumns[field_name]
        if second_choice:
            return second_choice[0]

    def set_opts(self, icons=True, scroll='xy', expand=True, width=None):
        """
        Modify default appearance of some features:
        
        - noicons: hide the icons
        - scroll:  (x, y, None)
        - expand: should the parent of this table expand?
        - width: set the maximum width of the widget
        """
        if not icons:
            self.widgets['A.icons'].hide()
        if not scroll:
            self.widgets['S=tree'].set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        else:
            if 'x' not in scroll:
                xpolicy = gtk.POLICY_NEVER
            else:
                xpolicy = gtk.POLICY_AUTOMATIC
            if 'y' not in scroll:
                ypolicy = gtk.POLICY_NEVER
            else:
                ypolicy = gtk.POLICY_AUTOMATIC
                
            self.widgets['S=tree'].set_policy(xpolicy, ypolicy)

        if width:
            self.treeview.set_property('width_request', width)
            


    def export(self, menuItem):
        """
        export visible data in csv format
        """
        import csv
        
        def next_row():
            for row in self.liststore:
                line = [self.gui_fields[f].get_human_value(getattr(row[0], f)) for f in self.field_list
                        if self.tvcolumns[f].get_property('visible')]
                yield line

        dialog = gtk.FileChooserDialog(_("Export in csv file"),
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_name("export.csv")
        
        filter = gtk.FileFilter()
        filter.set_name("csv files")
        filter.add_pattern("*.csv")
        dialog.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("all files")
        filter.add_pattern("*.*")
        dialog.add_filter(filter)

        ret = dialog.run()
        if ret == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            f = open(filename, "wb")
            writer = csv.writer(f)
            writer.writerows(next_row())
            f.close()
        dialog.destroy()
        return 

    def select_path(self, path=None, obj=None):
        """
        Select path ``path``. If path is null and obj is not null try finding path at which is obj
        """
        if path is None and obj:
            try:
                path = self.records.index(obj)
            except ValueError:
                pass

        if path is not None:
            self.treeview.get_selection().select_path(path)
            
#### completion

    def set_editable(self, editable=True):
        """
        Turn this table into a normal editable table
        table are not normally editable table if have relationship_mode = m2m
        """
        self.m2m_editable = editable
        for field in self.gui_fields:
            field.widget.add_completion(editable=editable)
        
