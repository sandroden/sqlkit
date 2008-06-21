from table import SqlTable
import sys
sys.path.append ('../../../')
#from sqlalchemy import *
#import layout
from datetime import datetime
import sqlalchemy.types as sqltypes
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

class SqlTable2(SqlTable):
    """A class that implements a different approach to record management and
    uses a listore with one single object (the instance) and a function to
    set the value in the cell via
                   column.set_cell_data_func
    """


    __metaclass__ = dbg.LogTheMethods

    
    def mapToListStore(self):
        self.liststore = gtk.ListStore(object)
        pass
    
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
    
    def set_fkey_descr(self, column, cell, model, iter, field_name):
        """cell_data_function used by column that have fkey
        """
        #dbg.show_caller(loc=False)
        fkey = getattr(model.get(iter, 0)[0], field_name)
        path = model.get_path(iter)
        #dbg.write("FKEY", fkey, path, i+1)
        #field_name = self.field_list[i]
        value = self.completion._lookup_value(field_name, fkey)
        #dbg.write(i, field_name, fkey, value)
        cell.set_property('text', value)
        
    def setupTreeColumns(self):
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
            elif issubclass(self.fields[v]['db_type'], (sqltypes.Date)):
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
            elif issubclass(self.fields[v]['db_type'], (sqltypes.DateTime)):
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
                length = re.search('(\d*)', self.fields[v]['col_spec']).group(1)
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
            
    def handle_fresh_data(self, records, fields, session):
        self.records = records
        return sqldata.SqlData(records, self.fields, self.session)
    
    def record_display(self, index=None):

        if index == None:
            self.liststore.clear()
            indexes = range(self.sqlData.count())
        else:
            #dbg.write('type index', type(index), index)
            indexes = [int(index)]
            
        for record in self.records:
            self.liststore.append([record])

    
        self.sb("Total N. of records: %s" % (len(self.liststore)))
        
    def set_value_real(self, field_name, value, path):

        dbg.write("%s" % self.liststore[path][0], field_name, value)
        setattr(self.liststore[path][0], field_name, value)
        return True
    
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
            but get_idx_of_selected() supposes that just one row is returned
            """

            obj = model[path][0]
            self.session.delete(obj)
            model.remove(iter)
            
        sel = self.treeview.get_selection()
        model, paths = sel.get_selected_rows()
        sel.selected_foreach(do_del)
        self.commit()

        ## select the same row or the preceding
        row_n = paths[0][0]  # path is a tuple here
        if row_n >= len(model):
            row_n -= 1
        sel.select_path(row_n)
        
        self.deleting_row = False

        self.sb("total N. of records: %s" % len(self.liststore))
        return True
    
    def record_save(self, ev = None, constraint={}):

        """save the record

        Detects if any editing has been done consulting self.model_path set
        by text_editing_started_cb.

        Detects if INSERT or UPDATE mode by analizing _sqlkit_mode

        see record_validate for constraint explanation
        """
        dbg.write("model_path", self.model_path)
        #import pdb; pdb.set_trace()
        if self.model_path is None: # no editing done
            dbg.write('no self.model_path, nothing to save', self.model_path)
            return
        
        obj = self.liststore[self.model_path][0]
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

        ### refresh the data
        #idx = self.sqlData.current
        #self.liststore[self.model_path][0] = idx
        #self.model_path = None
        #self.record_display(index=idx)

        
    def get_current_record(self):
        """returns the corrently selected obj"""
        row_n = self.get_selected_row()
        obj = self.model[row_n][0]

        ## FIXME:  why this?
        if not obj:
            obj = self.mapper.class_

        return obj
    
    def record_new(self, widget=None, *args):
        if self.block:
            dialog = self.message(type='error', title='Save needed',
                        text='Editing blocked until other field saved')
            if self.response == gtk.RESPONSE_OK:
                dialog.destroy()
            return

        self.record_save()
        ## scroll_to_cell will trigger selection_changed_cb
        ## when the new_obj has been added but not yet edited.
        ## we inhibit this 
        commit_allowed_status = self.commit_allowed
        self.commit_allowed = False


        # get the first visible col to position the cursor on
        columns = self.treeview.get_columns()
        for field in self.field_list:
            if self.tvcolumns[field].get_visible() and self.fields[field]['edit']:
                col = self.tvcolumns[field]
                break

        #dbg.write(dir(self.liststore))
        self.treeview.get_toplevel().set_focus(None)
        new_obj = self.mapper.class_()
        new_obj._sqlkit_mode = 'INSERT'
        self.session.save(new_obj)
        dbg.write(new_obj, vars(new_obj))
        path = self.liststore.get_path(self.liststore.append([new_obj]))
        dbg.write('appended new empty obj')
        self.treeview.scroll_to_cell(path, col)
        self.treeview.set_cursor(path = path,
                                 focus_column = col,
                                 start_editing = True)
        self.commit_allowed = commit_allowed_status
#        self.commit_allowed = commit_allowed
        #dbg.write('row_commit', self.commit_allowed)
        return True
        
