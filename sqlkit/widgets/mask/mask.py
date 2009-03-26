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
import gtk

#NOT_NULL_COLOR = gtk.gdk.color_parse('yellow')
FK_COLOR = gtk.gdk.color_parse('navyblue')
LBL_HOOVER_STYLE = gtk.gdk.color_parse('red')

class SqlMask(sqlwidget.SqlWidget):
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
        """
        Prepare for a new record
        """
        #current_idx = dbg.TraceIt(0, name='current_idx', mode='rw')

        sqlwidget.SqlWidget.__init__(self, *args, **kw)
        ## idle so that possible defaults get a chanche to be effective
        gobject.idle_add(self.record_new_idle)

####### Record browsing & saving
    def reload(self, **kw):

        changed = self.record_has_changed()

        if changed:
            skip_new = False
        else:
            skip_new = self.current
            
        response = self.save_unsaved(skip_check=changed, skip_new=skip_new)
        if response == gtk.RESPONSE_CANCEL:
            return
            
        self.current_idx = 0
        length = sqlwidget.SqlWidget.reload(self, **kw)
        if not length:
            self.record_new()
        return length

    def record_display(self, record=None, incr=0, index=None, check=True):
        """display an object record in the mask

        display the data provided by self.records[self.current + incr]
        incr: incr=incr 
        """
        if not self.records:
            ## TIP: message in the statis bar
            self.sb(_('No record present'), seconds=5)
            return
        if check:
            try:
                self.record_save(ask=True)
            except (exc.CancelledAction, exc.ValidationError):
                return

        if index is not None:
            display_idx = index
        else:
            display_idx = (self.current_idx or 0) + incr 

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

        for field in self.gui_fields:
            value = getattr(obj, field.field_name)
            self.set_value(field.field_name, value, initial=True)

        self.set_arrows_sensitivness(display_idx)
        return True

    def set_arrows_sensitivness(self, display_idx=None):
        """
        set sensitivness of back and forward arrows according to records length and position
        """
        if display_idx is None:
            display_idx = self.current_idx or 0

        self.ui_manager.get_action('/Main/Go/Forward').set_sensitive(display_idx+1 < len(self.records))
        self.ui_manager.get_action('/Main/Go/Back').set_sensitive(display_idx > 0)

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

    def set_value(self, field_name, field_value, fkvalue=None, initial=False, shown=False):
        """
        invoke field.set_value
        
        fkvalue: compatibility with SqlTable's one
        """

        if field_name not in self.gui_fields:
            raise exc.FieldNotInLayout("field_name: %s" % (field_name))

        self.gui_fields[field_name].set_value(field_value, initial=initial, shown=shown)

        if not initial:
            self.run_hook('on_change_value', field_value, fkvalue, field_name=field_name)
    
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
            text = _("Delete this record?\n(%s)" % self.current)
            response = self.dialog(type='ok-cancel', text=text)
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

        self.clear_mask(check=False)
        if not self.records:
            self.record_new()
        else:
            if self.current_idx  > len(self.records) -1:
                self.current_idx -= 1
            self.record_display(index=self.current_idx)
    
    def record_save(self, ask=True, new_obj=False, *args):
        """
        invokes the validator before UPDATE/INSERT a record
        ask:  ask if save is required
        new_obj:   the record is new. It forces mask2obj to skip check and save all fields
        """

        if not new_obj and not self.record_has_changed() and not (
            self.unsaved_changes_exist(skip_new=self.current)):
            self.sb(_('Nothing to save'), seconds=4)
            return

        if ask:
            response = self.save_unsaved(skip_check=True, proceed=False)

            if response == gtk.RESPONSE_CANCEL:
                raise exc.CancelledAction

            if response == gtk.RESPONSE_NO: 
                return
            
        obj = self.record_mask2obj(self.current, force=new_obj)
                
        self.record_validate(obj, single_fields=False)
            
        self.commit()
        self.last_new_obj = None
        
        self.record_display(check=False)
        
    def record_save_new(self, wdg, constraint={}):
        """
        create a new record by cloning the present
        """

        ## if PKey is editable we should add a check that is not the same
        if isinstance(self.tables, list):
            tbl = self.tables[0]
        else:
            tbl = self.tables
        for key in self.mapper_info.get_pkeys(tbl):
            if key in self.gui_fields and self.is_editable(key):
                if not self.gui_fields[key].has_changed():
                    self.dialog(text=_("Primary key (%s) didn't change. Refusing to save as new" % key))
                    return
            
        ## missing handling of Primary Key:
        ## should I delete the old one? should I look for editable attribute of the
        ## gtk widget?

        self.record_new(clear=False)
        try:
            self.record_save(ask=False, new_obj=True)
        except exc.ValidationError, e:
            pass
        
    def record_mask2obj(self, obj=None, force=False):
        """
        collect data from the mask and set into the object if record_has_changed())
        """
        if not obj:
            return obj

        if obj not in self.session: ## it should never happen, really... why do we need?
            self.session.add(obj)

        if force or self.record_has_changed():
            self.validation_errors = {}

            for field in self.gui_fields:
                field_name = field.field_name
                try:
                    value = self.gui_fields[field_name].get_value()
                    self.gui_fields[field_name].validate( value , clean=True)

                    if field.mapper:   # persisted fields, mask2obj has already cleaned  them
                        setattr(obj, field_name, self.get_value(field_name))

                except exc.ValidationError, e:
                    self.handle_validation_errors(e, field_name=field_name)

#             if self.validation_errors:
#                 self.validation_error_dialog()
        return obj

    def clear_mask(self, widget=None, check=True):
        """
        clear the mask for a new record
        NOTE: this does NOT prepare for a new record (missing obj)
        """

        if check and not self.save_unsaved():
            return

        self.current = None
        
        for field in self.gui_fields:
            self.clear_value(field.field_name)

    clear = clear_mask
    
    def record_new_idle(self):
        """
        record_new has been asked with idle_add from __init__
        when no info on possible .reload() was available.
        create a new record only if no records are present
        """
        if not self.records:
            self.record_new()

    def record_new(self, widget=None, clear=True):
        """
        prepare a new object and set
        clear = True/False. clear=False is used when 'saving as'
        """
        if self.current:
            if clear and not self.record_has_changed():
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

        self.set_arrows_sensitivness()

        self.current = self.get_new_object()
        self.last_new_obj = self.current
        self.records += [self.current]
        self.current_idx = len(self.records) -1
        self.sb(_("New record %s") % (self.current_idx +1))
        self.current_mode = 'INSERT'
        
    def record_undo_cb(self, menuItem):
        """
        undo possible modification to the mask
        """
        self.discard_changes()
        self.record_display(check=False)
        
    def record_forward_cb(self, widget):
        """
        display the next record in the mapper"""

        self.grab_focus(widget)
        return self.record_display(incr=1)
    
    def record_back_cb(self, widget):
        """
        display the previous record in the mapper"""
        
        self.grab_focus(widget)
        return self.record_display(incr=-1)
    
    def add_wheel_support(self):
        """
        add mouse wheel support
        """
        if not self.widgets['Window']:
            return
            
        def scroll_event_cb(widget, event):
            if not self.actiongroup_browse.get_sensitive():
                return
            
            if event.direction == gtk.gdk.SCROLL_UP:
                return self.record_display(incr=-1)
            else:
                return self.record_display(incr=1)

        self.widgets['Window'].connect('scroll_event', scroll_event_cb)


    def clear_cb(self, accell_group, window, ord, flags):
        self.record_new()

    def record_save_cb(self, widget, *args):
        """
        recard save callback...
        """
        self.grab_focus(widget)

        try:
            self.record_save(None)
        except (exc.CancelledAction, exc.ValidationError):
            pass

####### Layout, Reflection & Analisys

    def _get_layout(self, lay, naked):
        self.lay_obj, self.widgets  = sqlwidget.SqlWidget._get_layout(self, lay, naked)

        self._add_click_for_filter()
        self._add_color_to_labels()
        self.add_wheel_support()

        return self.lay_obj, self.widgets  
        
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
            
    def prepare_actions(self):
        """
        Prepare action needed by UIManager
        """
        sqlwidget.SqlWidget.prepare_actions(self)

        self.actiongroup_edit.add_actions([
            ('New', gtk.STOCK_NEW,   None, '', None, self.record_new_cb),
            ('Save-as', gtk.STOCK_SAVE_AS, None, None, None, self.record_save_new),
            ('Undo', gtk.STOCK_UNDO, None, None, None, self.record_undo_cb),
            ])

        self.actiongroup_edit.add_actions([
            ('Delete', gtk.STOCK_DELETE, None, '', None, self.record_delete),
            ])

    def prepare_uimanager(self):

        from sqlkit.widgets.common import uidescription
        
        sqlwidget.SqlWidget.prepare_uimanager(self)

        self.ui_manager.add_ui_from_string(uidescription.MASK_UI)


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
    
    














