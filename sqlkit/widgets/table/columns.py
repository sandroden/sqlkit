# Copyright (C) 2009, Sandro Dentella <sandro@e-den.it>
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
Classes that implement creation of column and cell renderers
This should allow to be as generic as possible while adding new renderers

Each Column widget need a 'master' argument that is the SqlWidget
in editing_started_cb and  edited_cb to set state variables on SqlWidget

"""


import gtk
import pango
import cell_renderers
from sqlkit import debug as dbg, _
from sqlkit.layout import widgets

class GenericColumn(object):
    RENDERER = gtk.CellRendererText
    RESIZE = True
    REORDER = True
    CLICK = True
    EXPAND = True
    MIN_DEFAULT_WIDTH = 4
    MAX_DEFAULT_WIDTH = 30

    def __init__(self, master, field_name, title):
        """
        Generic column with cell render setup
        """
        self.master = master 
        self.field_name = field_name
        self.column = self.setup_column(title)
        cell = self.setup_cell_renderers()
        self.column.set_cell_data_func(cell, self.cell_data_func_cb, 'text') 
        self.column.cells_data_func = [(cell, self.cell_data_func_cb, 'text') ]

    def setup_column(self, title):
        """
        setup column 
        """
        
        column = gtk.TreeViewColumn(title.replace('_',' '))
        column.set_data('field_name', self.field_name)  # used when reordering columns
        column.set_resizable(self.RESIZE)
        column.set_expand(self.EXPAND)
        column.set_reorderable(self.REORDER)
        column.set_clickable(self.CLICK)
        
        column.set_expand(self.is_expandable())
        column.connect('clicked', self.clicked_cb)
        self.add_header_widget(column)
        return column

    def setup_cell_renderers(self, cell_renderer=None):
        """
        setup cell renderers 
        """

        cell = cell_renderer or self.RENDERER()
        self.cell_set_property(cell)

        self.column.pack_start(cell, True)
        
        ## connect
        cell.connect('edited', self.edited_cb)
        cell.connect('editing-started', self.editing_started_cb)
        cell.connect('editing-canceled', self.editing_canceled_cb)

        return cell

### callback
    def edited_cb(self, cell, path, new_text):
        """
        callback on signal 'edited' on cell_renderer. 
        
        """

        ## NOTE: liststore.clear will trigger text_edited_cb!!!
        if self.master.deleting_row:
            return True

        if self.master.edited_row_model_path is None:
            return True

        if self.master.cell_entry and self.master.cell_validate():
            self.master.cell_entry = None
        else:
            return True

    def editing_started_cb(self, cell, editable, path):

        self.master.currently_edited_field_name = self.field_name
        self.master.initialize_record_editing(path)
        return True
    
    def cell_data_func_cb(self, column, cell, model, iter, prop_name):
        """
        function set by set_cell_data_func
        gets the attribute from the record and returns it
        """

        if not column.get_visible():
            return
        obj = model.get_value(iter, 0) 
        value = getattr(obj, self.field_name)
        cell.set_property(prop_name, value)        
        formatted_value = self.master.gui_fields[self.field_name].format_value(value)

        if isinstance(obj, self.master.totals.total_class):
            obj.set_value_and_colors(cell, formatted_value, self.field_name)
        else:
            cell.set_property(prop_name, formatted_value)        
            cell.set_property('foreground-set', False)
            cell.set_property('cell-background-set', False)
        

    def editing_canceled_cb(self, widget):
        """
        clean-up of cell_entry and restore value
        """

        if self.master.cell_entry and self.master.cell_entry.substitute:
            # assigning a value to liststore, triggers 'editing-canceled'
            self.master.cell_entry.substitute = False
            return
        
        self.master.set_value(self.field_name, self.master.gui_fields[self.field_name].initial_value)
        self.master.cell_entry = None

        self.master.sb(_("Editing canceled. Restoring original value"), seconds=3)
        
        
    def editable_connects(self, editable):
        """
        add here possible connect
        """
        pass
        
    def clicked_cb(self, treeview):
        """
        popup the menu on the header of the column
        """
        event =   gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
        event.button = 1
        self.master.popup_col_menu(event, self.field_name)
        
        return True
    
    
    def button_press_cb(self, widget, event, column):
        """
        popup the menu on the header of the column
        """
        ## this is not working at the moment.
        ## click on the label inside the eventBox don't propagate the button-press-event...
        self.master.popup_col_menu(event, self.field_name)
        
        return True
    
#### auxiliary
    def cell_set_property(self, cell):
        """
        set cell properties
        """
        
        if self.master.is_editable(self.field_name):
            cell.set_property('editable', True)
            cell.set_property('editable-set', True)
            cell.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        else:
            try:
                cell.set_property('editable', False)
            except:
                cell.set_property('sensitive', False)
                
        
    def add_header_widget(self, column):
        """
        Add a header that accepts tooltips and bold labels for mandatory columns
        """
        # Label
        label_text, help_text = self.master.label_map.get(self.field_name, (None, None))
        label_text = self.master.get_label(label_text or self.field_name)
        label = gtk.Label()
        label.set_markup(label_text)

        ## bold italic
        if not self.master.is_nullable(self.field_name) and not (
            self.master.mapper_info.fields[self.field_name]['default']):
            label.set_markup('<b><i>%s</i></b>' % label_text)

        # EventBox
        event_box = gtk.EventBox()
        event_box.add(label)
        event_box.show_all()

        # Tooltip
        if help_text:
            event_box.set_tooltip_text(help_text)

        # Header
        column.set_widget(event_box)
        event_box.connect('button-press-event', self.button_press_cb, column)


    def is_expandable(self):
        """
        make expandable only Strings with n_chars > 20 or Text
        """

        if self.master.is_text(self.field_name):
            return True
        if self.master.is_string(self.field_name):
            if self.master.mapper_info.fields[self.field_name]['length'] > 20:
                return True
        return False

    def get_width(self):
        """
        Find the width looking in default database info or in col_width
        """

        if self.master.col_width and self.field_name in self.master.col_width:
            width = self.master.col_width.get(self.field_name, )
        else:
            width = self.master.gui_fields[self.field_name].length

            if not width or width < self.MIN_DEFAULT_WIDTH:
                width = self.MIN_DEFAULT_WIDTH

            if width > self.MAX_DEFAULT_WIDTH:
                width = self.MAX_DEFAULT_WIDTH

        return width

    
    def __repr__(self):
        return "<%s: %s >" % (self.__class__.__name__, self.field_name)

class BooleanColumn(GenericColumn):
    RENDERER = gtk.CellRendererToggle
    RESIZE = False
    EXPAND = False

    def setup_cell_renderers(self, cell_renderer=None):
        """
        setup different cell_cb according to nullable value
        """

        cell = cell_renderer or self.RENDERER()
        self.cell_set_property(cell)

        self.column.pack_start(cell, True)
        
        ## connect
        cell.connect('editing-canceled', self.editing_canceled_cb) # ???
        cell.connect('toggled', self.toggled_signal_cb, self.master.liststore)
            
        self.column.set_cell_data_func(cell, self.cell_data_func_cb)
        self.column.cells_data_func = [(cell, self.cell_data_func_cb)]
        cell.fixed_width = True
        return  cell
        
    def cell_set_property(self, cell):

        cell.set_property('activatable', True)

    def toggled_signal_cb(self, cell, path, model):
        """
        callback that cicle into True/False/(inconsistent if nullable)
        """

        self.master.currently_edited_field_name = self.field_name
        self.master.initialize_record_editing(path)

        obj = self.master.liststore[path][0]
        status = getattr(obj, self.field_name)

        if self.master.is_nullable(self.field_name):
            # status may be True/False/None - I want to cicle
            if   status == True:    status = False
            elif status == False:   status = None
            elif status == None:    status = True
        else:
            status = not status

        self.master.gui_fields[self.field_name].set_value(status, initial=False )        
            
        return True
    
    def cell_data_func_cb(self, column, cell, model, iter, prop_name):
        """
        function set by set_cell_data_func for nullable boolean
        """

        if not column.get_visible():
            return
        
        obj = model.get_value(iter, 0) 
        value = getattr(obj, self.field_name)
        cell.set_property('active', value)        

        if isinstance(obj, self.master.totals.total_class):
            cell.set_property('visible', False)        
        else:
            cell.set_property('visible', True)        

            if value is None:
                cell.set_property('inconsistent', True)
            else:    
                cell.set_property('inconsistent', False)
        
class VarcharColumn(GenericColumn):
    """
    A renderer that expands only large fields and that centers text if it's little
    Cell renderer is choosen according to VarChar or Text
    """
    __metaclass__ = dbg.LogTheMethods
    
    def setup_cell_renderers(self, cell_renderer=None):

        width = self.get_width()

        ## look for a possibly defined width
        ## choose cell renderer
        if width:
            cell = cell_renderers.CellRendererVarchar(width)
            cell.fixed_width = True
        else:
            cell = gtk.CellRendererText()

        GenericColumn.setup_cell_renderers(self, cell_renderer=cell)
        cell.set_property('ellipsize', pango.ELLIPSIZE_END)

        self.set_alignment(cell)
        return cell

    def set_alignment(self, cell):
        """
        Set alignment of text in the cell
        """
        
        length = self.master.gui_fields[self.field_name].length
        if length:
            try:
                ## if field has less then 4 chars, position it in the middle
                if int(length) <= 4:
                    cell.set_property('xalign', 0.5)
            except:
                pass
        return  cell


    def editing_started_cb(self, cell, editable, path):
        """
        prepare the editable, completion and validation
        """
        self.master.currently_edited_field_name = self.field_name
        self.master.cell_entry = CellEntry(editable, cell, path, self.field_name)
        editable.connect('remove-widget', self.remove_widget_cb)
        editable.connect('key-press-event', self.master.keypress_event_cb)
        editable.connect('focus-out-event', self.focus_out_cb, cell, path)
        self.editable_connects(editable)
        
        self.master.fkey_value = editable.get_text()
        
        if hasattr(self.master.field_widgets[self.field_name], 'completion'):
            completion = self.master.field_widgets[self.field_name].completion
            if completion and not self.master.is_text(self.field_name):
                completion.add_completion(editable)
                completion.add_callbacks(editable)
            
        ## MAX LENGTH
        self.master.field_widgets[self.field_name].field.set_max_length()
                
        self.master.initialize_record_editing(path)
        self.master.commit_inhibited = False
        return True

    def remove_widget_cb(self, widget):
        """
        If the call has invalid data we don't want to remove the widget
        so that we can edit the wrong data rather then loosing what was already typed
        """
        if self.master.cell_entry and not self.master.cell_entry.is_valid():
            widget.stop_emission('remove-widget')
            return True
        self.master.cell_entry = None

    def focus_out_cb(self, widget, event, cell, path):
        if self.master.cell_entry:
            widget.activate()

class MultilineColumn(VarcharColumn):
    """
    A renderer able to show and edit in multiline mode. Very basic...
    """

    
    def setup_cell_renderers(self, cell_renderer=None):

        width = self.get_width()

        cell = cell_renderers.MultilineCellRenderer(self.master)

        GenericColumn.setup_cell_renderers(self, cell_renderer=cell)
        cell.set_property('ellipsize', pango.ELLIPSIZE_END)

        return cell

    def remove_widget_cb(self, widget):
        """
        If the call has invalid data we don't want to remove the widget
        so that we can edit the wrong data rather then loosing what was already typed
        """
        if self.master.cell_entry:
            self.master.cell_validate()

        self.master.cell_entry = None

    def focus_out_cb(self, widget, event, cell, path):

        if self.master.cell_entry:
            self.master.cell_validate()
            cell.emit("edited", cell.editor.get_data("path"), cell.editor.get_text())
            cell.editor.remove_widget()

        pass

class NumericColumn(VarcharColumn):
    """
    A renderer similar to varchar but with different expand options
    and with right justification
    """
    
    def get_width(self):
        
        if self.master.col_width and self.field_name in self.master.col_width:
            width = self.master.col_width.get(self.field_name, )
        else:
            if self.master.gui_fields[self.field_name].type == int:
                width = 8
            else:
                width = self.master.gui_fields[self.field_name].column.type.precision

    def set_alignment(self, cell):

        cell.set_property('xalign', 1.0)

    def editable_connects(self, editable):
        editable.connect('key-press-event', self.master.digits_check_input_cb  )            


class FKeyColumn(VarcharColumn):
    """
    A renderer that shows the value instead of the id
    """

    def cell_set_property(self, cell):

        VarcharColumn.cell_set_property(self, cell)
        cell.set_property('foreground', 'navyblue')
        
    def cell_data_func_cb(self, column, cell, model, iter, prop_name):
        """
        cell_data_function used by column that have fkey
        """

        if not column.get_visible():
            return

        obj = model.get_value(iter, 0)
        
        if not obj:
            return
        
        if isinstance(obj, self.master.totals.total_class):
            cell.set_property('text', '')

        else:
            fkey_value = getattr(obj, self.field_name)

            if fkey_value is not None:
                path = model.get_path(iter)
                value = self.master.completions[self.field_name].lookup_value(fkey_value)
                cell.set_property('text', value)
            else:
                cell.set_property('text', '')

    
class DateColumn(VarcharColumn):

    """
    Will have bindings to change the date in a faster way
    possibly popping a calendar
    """

    MIN_DEFAULT_WIDTH = 8
    
    def editable_connects(self, editable):

        pass
        #editable.connect('key-press-event')
    
class DateTimeColumn(DateColumn):

    MIN_DEFAULT_WIDTH = 16
    
    def editable_connects(self, editable):

        pass
        #editable.connect('key-press-event')
    
class CellEntry(object):
    """
    An object to store info on editable status
    Mainly needed to check if validation is required with FKey fields and m2m nested tables
    Completion sets valid to True, any manual edit invalidates, so that a field.validate() is
    triggered.
    Any movement (click of Tab or Down) away from a CellRenderer is inhibited if

      * a cell exists
      * the cell is not valid
      
    CellEntry is destroyed within 'remove-widget' signal callback of the editable

    FIXME: should probably be simplified being it only needed for FKey Columns/m2m
    """
    def __init__(self, editable, cell, path, field_name):

        self.entry = editable
        self.cell = cell
        self.path = path
        self.field_name = field_name
        self.valid = True
        self.text = editable.get_text()

        if isinstance(editable, gtk.Entry):
            # Multiline does not have 'canged' and does not need invalidating
            self.entry.connect('changed', self.on_editable_change)
        else:
            ## this is just a hack to force cell_validate() when browsing away
            self.valid = False
            
        self.substitute = False

    def on_editable_change(self, widget):
        self.valid = False

    def is_valid(self):
        
        valid = self.valid or self.text == self.entry.get_text()
        return valid

    def get_text(self):
        return self.entry.get_text()
    
    def __repr__(self):
        return "<CellEntry: (%s) %s>" % (self.valid, self.get_text())
