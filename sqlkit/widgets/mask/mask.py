import sys, re, datetime
import layout
import layout.dateedit as dateedit

import gtk, pango
from sqlalchemy import *
from sqlalchemy.exc import InvalidRequestError
from sqlkit.widgets.common.fields import FieldChooser
import sqlkit
from sqlkit.validation import validator
from sqlkit.widgets.common import completion, sqlwidget
import decimal
import sqlkit
import dbg

class FieldNotInLayout(Exception): pass
class FieldValueNotSet(Exception): pass
class CancelledAction(Exception): pass

#NOT_NULL_COLOR = gtk.gdk.color_parse('yellow')
FK_COLOR = gtk.gdk.color_parse('navyblue')
LBL_HOOVER_STYLE = gtk.gdk.color_parse('red')

class SqlMask (sqlwidget.SqlWidget):
    """doc string for sqlmask
    """

    __metaclass__ = dbg.LogTheMethods
    vfields = None  # mask widgets: key: field_name  value: ( gtkClass, widgetName )
    labels   = None  # correspondance Label <-> EventBox
#    map_record_n = 0  # number of the displayed record within mapper
    row_count = 0    # number of records in the mapper
    #current = dbg.TraceIt(None, name='current', mode='rw')
    current = None
    current_idx = dbg.TraceIt(0, name='current_idx', mode='rw')
    current_mode = None
    def __init__(self, *args, **kw):
        """Prepare for a new record
        """

        sqlwidget.SqlWidget.__init__(self, *args, **kw)
        self.record_new()

####### Record browsing & saving
    def reload(self, **kw):

        if not self.save_unsaved():
            return
        self.current_idx = 0
        sqlwidget.SqlWidget.reload(self, **kw)

    def record_display(self, record=None, incr=0, index=None, reread=False):
        """display an object record in the mask

        display the data provided by self.records[self.current + incr]
        incr: incr=incr 
        """
        if not self.records:
            self.sb('No records to browse')
            return
        if not reread:
            try:
                self.record_save(None, ask=True)
            except CancelledAction:
                return

        if index is not None:
            display_idx = index
        else:
            display_idx = (self.current_idx or 0) + incr 

            #dbg.set_trace()
        try:
            assert display_idx >= 0  # no negative indexes
            obj = self.records[display_idx]
            self.clear_mask(check=False)
            self.current_idx = display_idx
            self.current = obj
            msg_info = "record %s/%s" % (display_idx +1, len(self.records))
        except (IndexError, AssertionError), e:
            msg_info = "record %s/%s" % (self.current_idx +1, len(self.records))
            if incr >= 0:
                self.sb('Already last ' + msg_info)
            else:
                self.sb('Already first ' + msg_info)
            return None


        self.sb(msg_info)
        for field_name in self.field_list:
            try:
                self.set_value(field_name, getattr(obj, field_name))
                #self.get_value(field_name) ????
            except FieldNotInLayout, e:
                pass

        #self.sync()
        self.actions.on_record_display(new=obj)
        #sqlwidget.SqlWidget.record_display(self, new=data_in)
        
        ## return True if a record has beeen displayed. In case we 2 Mask in sync
        ## this will stop the master mask to continue in the next record until
        ## the first has been terminated
        #dbg.write("%s DATA DISPLAYed " % self.nick)
        return True
        
    def set_value(self, field_name, field_value, fkvalue=None):
        """this is the method that knows how to handle different type of data
        if field_name is a FKey ending with _id, it retrieves the description,
        shows it in the entry but stores the id in self.values[field_name]

        fkvalue: compatibility with SqlTable's one
        """
        #dbg.write("%s: %s" % (field_name, field_value))
        if field_name not in self.vfields:
            raise FieldNotInLayout("field_name: %s" % (field_name))

        self.vfields[field_name].set_value(field_value)
        
        
    def clear_value(self, field_name):
        """clear the value
        """
        if field_name not in self.vfields:
            raise FieldNotInLayout("field_name: %s" % (field_name))

        self.vfields[field_name].set_default()
        
        
    def get_value(self, field_name, data=False, shown=False):
        """return the value from the widget
        """

        if field_name not in self.vfields:
            dbg.write("%s Non in vfields %s" % (field_name, self.vfields.keys()))
            raise FieldNotInLayout("field_name: %s" % (field_name))

        field = self.vfields[field_name]
        
        return field.get_value(shown=shown)

    def record_delete(self, widget=None, interactive=True):
        """invokes the validator before DELETing a record"""
            
        if interactive:
            response = self.dialog(type='ok-cancel', text="Delete this record?")
            if response == gtk.RESPONSE_CANCEL:
                return

        self.session.delete(self.records[self.current_idx])
        self.last_new_obj = None
        
        self.commit()
        self.records.pop(self.current_idx)
        if self.current_idx  > len(self.records) -1:
            self.current_idx -= 1
        self.record_display(index=self.current_idx)
    
    def record_save(self, ev, constraint={}, ask=True, *args):
        """invokes the validator before UPDATE/INSERT a record"""
        ## FIXME: validator
        
        #         if self.valid is not None:
        #             v = self.valid (self.table, record)
        #             v.validate ()

        if not self.record_has_changed():
            return

        obj = self.record_mask2obj(self.current)

        self.actions.on_save(obj, mode=self.current_mode)
    

        ##  FIXME: constraints
        #         if R.keys():
        #             R.update(self.constraint)
        #             R.update(constraint)
        #             dbg.write("CONSTRAINT:", R, constraint)
        #             self.sqlData.set(R)
        
        if ask:
            if not self.save_unsaved():
                raise CancelledAction
        else:
            self.commit()

        self.record_display(reread=True)
        self.current_mode = 'UPDATE'
        self.record_save_sync()
        
    def record_save_new(self, wdg, constraint={}):
        """create a new record by cloning the present
        """

        ## if PKey is editable we should add a check that is not the same
        if isinstance(self.tables, list):
            tbl = self.tables[0]
        else:
            tbl = self.tables
        for key in self.fields.get_pkeys(tbl):
            if key in self.vfields and self.is_editable(key):
                raise NotImplemented
            
        ## missing handling of Primary Key:
        ## should I delete the old one? should I look for editable attribute of the
        ## gtk widget?

        self.record_new(clear=False)
        try:
            self.record_save(self.current)
        except InvalidRequestError, e:
            print e.message
            raise
        
    def record_mask2obj(self, obj=None):
        """collect data from the mask and set into the object if record_has_changed())
        """
        if not obj:
            return obj


        if self.record_has_changed():
            if obj not in self.session:     # see note in record_new
#                 for i in self.session:
#                     print i, id(i)
#                 print "OBJ:", obj, id(obj), obj not in self.session
                self.session.add(obj)
                
            for field_name in self.field_list:      
                try:
                    value = self.get_value(field_name)
                except FieldNotInLayout:
                    continue

                #print "setattr(obj, %s, %s)" % (field_name, self.get_value(field_name))
                setattr(obj, field_name, self.get_value(field_name))

        return obj

    def clear_mask(self, widget=None, check=True):
        """clear the mask for a new record
        NOTE: this does NOT prepare for a new record (missing obj)
        """

        if check and  not self.save_unsaved():
            return

#        self.current_idx = None
        self.current = None
        
        for field_name in self.field_list:
            try:
                self.clear_value(field_name)
            except FieldNotInLayout, e:
                pass

        ## sync
        for z in self.sync_dict:
            z.clear()
            z.sync_block()
            
    clear = clear_mask
    
    def record_new(self, widget=None, clear=True):
        """prepare a new object and set 
        """
        if clear:
            self.clear_mask()

        self.current = self.get_new_object()
        self.records += [self.current]
        self.current_idx = len(self.records) -1
        self.sb("New record %s" % (self.current_idx +1))
        self.current_mode = 'INSERT'
        
    def record_forward(self, ev):
        """display the next record in the mapper"""

        return self.record_display(incr=1)
    
    def record_back(self, ev):
        """display the previous record in the mapper"""
        
        return self.record_display(incr=-1)
    
    def add_accelerators(self):
        """
        C-S-n clear
        C-s  save- record
        """
        
        sqlwidget.SqlWidget.add_accelerators(self)

        self.accel_group.connect_group(
            ord('n'), gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK,  
            gtk.ACCEL_LOCKED, self.clear_cb)

        self.accel_group.connect_group(
            ord('s'), gtk.gdk.CONTROL_MASK,
            gtk.ACCEL_LOCKED, self.record_save_cb)
    def clear_cb(self, accell_group, window, ord, flags):
        self.record_new()
        
    def record_save_cb(self,  accell_group, window, ord, flags):
        try:
            self.record_save(None)
        except CancelledAction:
            pass

    def unsaved_changes_exist(self):
        """collect possible changes and test if save is needed
        """

        self.record_mask2obj(self.current)
        return sqlwidget.SqlWidget.unsaved_changes_exist(self)
        
####### Sync
    def record_back_sync(self, incr=1):
        for z in self.sync_dict:
            if isinstance(z, sqlkit.SqlMask):
                return z.record_back('')
        return False
    
    def record_forward_sync(self, incr=1):
        for z in self.sync_dict:
            if isinstance(z, sqlkit.SqlMask):
                return z.record_forward('')
        return False
            
    def record_save_sync(self):
        for w, value in self.sync_dict.iteritems():
            w.sync_unblock()
            dbg.write(w, value)
            DIR, sql, fields_dict = value
            val = {}
            ### FIXME: sqldata
            rdict = self.sqlData.get()
            dbg.write('rdict=',rdict)
            
            for name, referenced_name in fields_dict.iteritems():
                val[referenced_name] = rdict[name]

            w.record_save('', constraint=val)
#         for z in self.sync_dict:
#             z.record_save('')

####### Layout, Reflection & Analisys
    def _analize_widgets_in_layout(self):
        """fill variables from layout

        vfields
        --------
        is a dict: 
           :key:   is the field_name
           :value: is a field from sqlkit.widget.mask.fields

        """
        ## FIXME: does not work when renaming: euro.user_id -> euro_user_id

        ## vfields can be passed as argument of the class. In that case widgets
        ## used to represent the data are provided by another SqlMask
        if not self.vfields:
            self.vfields = {}
        ## by now I only use entry, date, radio, checbuttom, comboBox to represent data
        #dbg.dshow(self.w, 'e=')
#         if self.nick == 'art':
#             print self.w.keys()

        field_chooser = FieldChooser(self, self.w)

        for field_name in self.field_list:
            ## MM is a workarond to bypass the fact that if I use 'A'
            ## I'll ind *many* alignement for InterField
            for mod in ('e','d','r','c', 'TX', 'Ce', 'm2m', 'm2o', 'o2m', 'o2o'):
                try:
                    key = "%s=%s" % (mod, field_name)
                    widget = self.w[key]
                    field = field_chooser.get_field(field_name, self.fields[field_name], key)

                    self.vfields[field_name] = field
                    
                except KeyError, e:
                    pass
            
            # (gtkClass , gtkWidget)

        ## all EventBox 
        self.labels = {}
        for field_name in self.fields.keys():
            lbl_name_wdg = "l=%s" % field_name
            if lbl_name_wdg in self.w:
                self.labels[field_name] = self.w[lbl_name_wdg]
                #dbg.write("%s -> %s"% (field_name, self.labels[field_name]))
            else:
                #dbg.write("Missing event_box for %s" % (field_name))
                pass
    
    def toggle_with_null_cb(self, button):
        """a toggle function that loops through inconsinstent state also
        """
        value = v = button.get_active()
        null = n = button.get_inconsistent()

        ## -   -> True  -> False
        if null:  # - next is True
            button.set_active(True)
            button.set_inconsistent(False)
        else:
            dbg.write("Null False")
            if value == True:
                dbg.write('Vero passo a Falso')
                button.set_inconsistent(False)
                button.set_active(False) 
            else:
                dbg.write('False passo a Null')
                button.set_inconsistent(True)

        return True
            
            
            
    def _add_color_to_labels(self):
        """add bg colors and fonts to signal needed fields"""

        for field_name in self.fields.keys():
            if field_name in self.labels:
                lbl    = self.labels[field_name]
                ev_wdg = self.labels[field_name].parent

                ev_wdg.connect('enter-notify-event', self.ene_cb)
                ev_wdg.connect('leave-notify-event', self.lne_cb)
                lbl.modify_fg(gtk.STATE_PRELIGHT, LBL_HOOVER_STYLE)

                ## label FK_COLOR to tell it's a foreign key
                if self.fields[field_name]['fkey'] :
                    #dbg.write("FK", field_name)
                    self.labels[field_name].modify_fg(gtk.STATE_NORMAL, FK_COLOR)
                else:
                    #dbg.write("NO", field_name)
                    pass
            
    def ene_cb(self, eb, ev):
        eb.get_child().set_state(gtk.STATE_PRELIGHT)
        return True
    def lne_cb(self, eb, ev):
        eb.get_child().set_state(gtk.STATE_NORMAL)
        return True
        
    def _add_click_for_filter(self):
        """Add controls according to data type represented
        check on input for integers
        configuring date / datetime for time*
        adding focus-out staff
        adding tooltips and click for filter_panel
        """

        ## add click that pops filter_panel
        for field_name, label in self.labels.iteritems():
            #print "label", label, 'field_name', field_name
            event_box = label.parent
            event_box.connect('button-press-event',
                              self.filter_panel.add, field_name, self)

    def get_current_obj(self):
        """Return the object that is currently edited"""
        return self.current

    def get_widget(self, field_name):
        """get the widget that render field_name"""

        return self.vfields[field_name].widget.gtkwidget


####### Validation
    def focus_out__widget(self, widget, event, field_name):
        self.last_visited_field = field_name
        #print "focus_out", event, field_name
        
    def focus_in__widget(self, widget, event, more=None):
        #print "focus_in"
        #print "more: ",more
        pass
    
    
class Combo(SqlMask):
    """
    This is meant to edit a normal situation of header/rows (eg. invoices)
    table must be a list of two tables that will be synced automatically.

    The layout should be explicitally provided.
    """
    def _get_layout(self, lay, naked):
        lay, w = SqlMask._get_layout(self, lay, naked)
        if self.icons:
            icons = self.icons
        else:
            icons = 'b=gtk-delete b=gtk-new b=gtk-refresh'
            
        self.SqlTable = sqlkit.SqlTable(tables=self.tables[1],
                                        naked=True,
                                        layout=None,
                                        engine=self.engine,
                                        addto=self.w['A=table'],
                                        mode=self.mode,
                                        limit=0,
                                        nick="%s.%s" % (self.nick, self.tables[1]),
                                        actions=self.actions,
                                        field_list=self.table_field_list,
                                        icons=icons
                                        
                                        )
        self.sync_add(self.SqlTable)
        self.SqlTable.SqlMask = self
        # self.lay_obj.prop('TV=tree', 'height-request', 150)        

        if self.sql:
            self.reload(self.sql)
        else:
            pass
            self.clear_mask()
            
        return (lay, w)
    
    def get_mapper(self, mapper, tables):
        return self.dbproxy.get_mapper(mapper, tables[0])

    def parse_fields(self, fields):
        self.table_field_list = fields
        return SqlMask.parse_fields(self, None)














