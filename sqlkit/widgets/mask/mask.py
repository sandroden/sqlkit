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

import sys, re, datetime
from sqlkit import layout

import gtk, pango
from sqlalchemy import *
from sqlalchemy.exc import InvalidRequestError
from sqlkit.widgets.common.fields import FieldChooser
import sqlkit
from sqlkit.validation import validator
from sqlkit.widgets.common import completion, sqlwidget
import decimal
import sqlkit
from sqlkit import debug as dbg
from sqlkit import exc, _
import gobject

#NOT_NULL_COLOR = gtk.gdk.color_parse('yellow')
FK_COLOR = gtk.gdk.color_parse('navyblue')
LBL_HOOVER_STYLE = gtk.gdk.color_parse('red')

class SqlMask (sqlwidget.SqlWidget):
    """doc string for sqlmask
    """

    __metaclass__ = dbg.LogTheMethods
#    gui_fields = None  # mask widgets: key: field_name  value: ( gtkClass, widgetName )
    labels   = None  # correspondance Label <-> EventBox
    row_count = 0    # number of records in the mapper
    current_idx = 0
    current = None
    current_mode = None

    def __init__(self, *args, **kw):
        """Prepare for a new record
        """
        #current_idx = dbg.TraceIt(0, name='current_idx', mode='rw')

        sqlwidget.SqlWidget.__init__(self, *args, **kw)
        ## idle so that possible defaults get a chanche to be effective
        gobject.idle_add(self.record_new)

####### Record browsing & saving
    def reload(self, **kw):

        if not self.save_unsaved():
            return
        self.current_idx = 0
        length = sqlwidget.SqlWidget.reload(self, **kw)
        if not length:
            self.record_new()
        return length

    def record_display(self, record=None, incr=0, index=None, reread=False):
        """display an object record in the mask

        display the data provided by self.records[self.current + incr]
        incr: incr=incr 
        """
        if not self.records:
            ## TIP: message in the statis bar
            self.sb(_('No record present'), seconds=5)
            return
        if not reread:
            try:
                self.record_save(ask=True)
            except (exc.CancelledAction, exc.ValidationError):
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
            msg_info = "%s/%s" % (display_idx +1, len(self.records))
        except (IndexError, AssertionError), e:
            msg_info = "%s/%s" % (self.current_idx +1, len(self.records))
            if incr >= 0:
                self.sb(_('Already last record') + msg_info)
            else:
                self.sb(_('Already first record') + msg_info)
            return None


        self.sb(msg_info)

        for field_name in self.field_list:
            try:
                value = getattr(obj, field_name)
                dbg.write("VALUE (%s): %s" % (field_name, value))
                self.set_value(field_name, value)
                #self.get_value(field_name) ????
            except exc.FieldNotInLayout, e:
                pass

        #self.actions.on_record_display(new=obj)
        #sqlwidget.SqlWidget.record_display(self, new=data_in)
        
        ## return True if a record has beeen displayed. In case we 2 Mask in sync
        ## this will stop the master mask to continue in the next record until
        ## the first has been terminated
        #dbg.write("%s DATA DISPLAYed " % self.nick)
        return True

    def set_records(self, records, index=0):
        """
        set records to browse, and display number idx
        """
        self.clear_mask()
        self.records = records
        # it's handy to set set_records([table.current])
        # that may also be empty
        if records and not records == [None]: 
            self.record_display(index=index)
        self.record_refresh()

    def set_value(self, field_name, field_value, fkvalue=None, initial=True, shown=False):
        """
        invoke field.set_value
        
        fkvalue: compatibility with SqlTable's one
        """

        if field_name not in self.gui_fields:
            raise exc.FieldNotInLayout("field_name: %s" % (field_name))

        self.gui_fields[field_name].set_value(field_value, initial=initial, shown=shown)
        
        
    def clear_value(self, field_name):
        """
        clear the value
        """
        if field_name not in self.gui_fields:
            raise exc.FieldNotInLayout("field_name: %s" % (field_name))

        self.gui_fields[field_name].set_default()
        
        
    def get_value(self, field_name, data=False, shown=False):
        """
        return the value from the widget
        """

        if field_name not in self.gui_fields:
            dbg.write("%s Non in gui_fields %s" % (field_name, self.gui_fields.keys()))
            raise exc.FieldNotInLayout("field_name: %s" % (field_name))

        field = self.gui_fields[field_name]
        return field.get_value(shown=shown)

    def record_delete(self, widget=None, interactive=True):
        """
        delete a record
        """
            
        if interactive:
            response = self.dialog(type='ok-cancel', text=_("Delete this record?"))
            if response == gtk.RESPONSE_CANCEL:
                return
        obj = self.records[self.current_idx]
        if obj in self.session.new:
            self.session.expunge(obj)
        else:
            self.session.delete(obj)
        self.last_new_obj = None
        
        self.commit(_('Deleted'))
        self.records.pop(self.current_idx)

        if not self.records:
            self.clear_mask(check=False)
            self.record_new()
        else:
            if self.current_idx  > len(self.records) -1:
                self.current_idx -= 1
            self.record_display(index=self.current_idx)
    
    def record_save(self, ask=True, *args):
        """
        invokes the validator before UPDATE/INSERT a record
        """
        ## FIXME: validator
        
        #         if self.valid is not None:
        #             v = self.valid (self.table, record)
        #             v.validate ()

        if not self.record_has_changed() and not self.unsaved_changes_exist():
            if self.last_new_obj:
                ## very important: existence of an instance that is not
                ## persinstant will turn out in an error if it cannot be
                ## saved. That can occur also when simply setting a loader attribute.
                self.session.expunge(self.last_new_obj)
                self.current = None
                self.last_new_obj = None
            self.sb(_('Nothing to save'), seconds=4)
            return
        obj = self.record_mask2obj(self.current, skip_check=True)

        self.record_validate(obj)
    
        if ask:
            if not self.save_unsaved(skip_check=True):
                raise exc.CancelledAction
        else:
            self.commit()
            self.last_new_obj = None
        
        self.record_display(reread=True)
        self.current_mode = 'UPDATE'
        
    def record_save_new(self, wdg, constraint={}):
        """create a new record by cloning the present
        """

        ## if PKey is editable we should add a check that is not the same
        if isinstance(self.tables, list):
            tbl = self.tables[0]
        else:
            tbl = self.tables
        for key in self.mapper_info.get_pkeys(tbl):
            if key in self.gui_fields and self.is_editable(key):
                raise NotImplementedError
            
        ## missing handling of Primary Key:
        ## should I delete the old one? should I look for editable attribute of the
        ## gtk widget?

        self.record_new(clear=False)
        try:
            self.record_save()
        except exc.ValidateError, e:
            pass
        
    def record_mask2obj(self, obj=None, skip_check=False):
        """collect data from the mask and set into the object if record_has_changed())
        """
        if not obj:
            return obj


        if skip_check or self.record_has_changed():
            if obj not in self.session:     # see note in record_new
#                 for i in self.session:
#                     print i, id(i)
#                 print "OBJ:", obj, id(obj), obj not in self.session
                self.session.add(obj)
                
            for field_name in self.field_list:      
                try:
                    value = self.get_value(field_name)
                except exc.FieldNotInLayout:
                    continue

                #print "setattr(obj, %s, %s)" % (field_name, self.get_value(field_name))
                setattr(obj, field_name, self.get_value(field_name))

        return obj

    def clear_mask(self, widget=None, check=True):
        """clear the mask for a new record
        NOTE: this does NOT prepare for a new record (missing obj)
        """

        if check and not self.save_unsaved():
            return

        self.current = None
        
        for field_name in self.field_list:
            try:
                self.clear_value(field_name)
            except exc.FieldNotInLayout, e:
                pass

    clear = clear_mask
    
    def record_new(self, widget=None, clear=True):
        """
        prepare a new object and set
        clear = True/False. clear=False is used when 'saving as'
        """
        #dbg.set_trace()
        if self.current:
            if not self.record_has_changed():
                if self.last_new_obj:
                    self.sb(_("Already at new record"))
                    return

        if clear:
            try:
                if self.current:
                    ## this is important to trigger validation in time to prevent
                    ## a change in self.current. No need if all we want is to
                    ## 'save as new'
                    self.record_save()
                self.clear_mask(check=False)
            except exc.ValidationError:
                return

        self.current = self.get_new_object()
        self.last_new_obj = self.current
        self.records += [self.current]
        self.current_idx = len(self.records) -1
        self.sb(_("New record %s") % (self.current_idx +1))
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

    def record_save_cb(self,  *args):
        """accell_group, window, ord, flags or ev..."""
        try:
            self.record_save(None)
        except (exc.CancelledAction, exc.ValidationError):
            pass

    def unsaved_changes_exist(self, skip_check=False):
        """collect possible changes and test if save is needed
        """

        self.record_mask2obj(self.current, skip_check=skip_check)
        return sqlwidget.SqlWidget.unsaved_changes_exist(self)
        

####### Layout, Reflection & Analisys

    def setup_field_validation(self):
        """fill variables from layout

        gui_fields: validation fields
        --------------------------
        is a dict: 
           :key:   is the field_name
           :value: is a field from sqlkit.widget.mask.fields

        """
        ## gui_fields can be passed as argument of the class. In that case widgets
        ## used to represent the data are provided by another SqlMask
        from  pprint import pprint
        if not self.gui_fields:
            self.gui_fields = {}

        field_chooser = FieldChooser(self, self.widgets)

        for field_name, widget_key in self.laygen.fields_in_layout.iteritems():
            widget = self.widgets[widget_key]
            field = field_chooser.get_field(field_name, self.mapper_info.fields[field_name], widget_key)
            
            self.gui_fields[field_name] = field
            
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

        for field_name in self.mapper_info.fields.keys():
            if field_name in self.labels:
                lbl    = self.labels[field_name]
                ev_wdg = self.labels[field_name].parent

                ev_wdg.connect('enter-notify-event', self.ene_cb)
                ev_wdg.connect('leave-notify-event', self.lne_cb)
                lbl.modify_fg(gtk.STATE_PRELIGHT, LBL_HOOVER_STYLE)

                ## label FK_COLOR to tell it's a foreign key
                if self.mapper_info.fields[field_name]['fkey'] :
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

        ## all EventBox 
        self.labels = {}
        for field_name in self.mapper_info.fields.keys():
            lbl_name_wdg = "l=%s" % field_name
            if lbl_name_wdg in self.widgets:
                self.labels[field_name] = self.widgets[lbl_name_wdg]
                #dbg.write("%s -> %s"% (field_name, self.labels[field_name]))
            else:
                #dbg.write("Missing event_box for %s" % (field_name))
                pass
    
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

        return self.gui_fields[field_name].widget.gtkwidget

    def fkey_is_valid(self, field_name):
        """
        return True if current editable -if exists- has a value that does not need validation
        """
        return self.gui_fields[field_name].widget.is_valid()

####### Misc
    def export(self, menuItem):
        self.dialog(type="ok", text=_("Export feature available only for Tables"))

####### Validation
    def focus_out__widget(self, widget, event, field_name):
        self.last_visited_field = field_name
        #print "focus_out", event, field_name
        
    def focus_in__widget(self, widget, event, more=None):
        #print "focus_in"
        #print "more: ",more
        pass
    
    










