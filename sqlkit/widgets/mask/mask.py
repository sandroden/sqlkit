import sys, re, datetime
#import config
#import inspect
#import common
import layout
import layout.dateedit as dateedit

#import validator
from sqlkit.widgets.common.layoutgenerator import LayoutGenerator
import gtk, pango
from sqlalchemy import *
import dbg.gtk_dbg
import sqlkit
#from sqlkit.widgets.common import sqlfilter
#from sqlkit.db import sqldata
#import sqlkit.sqldata as sqldata
#import sqlkit.inspect as sinspect
from sqlkit.validation import validator
from sqlkit.widgets.common import completion, sqlwidget
import decimal
import sqlkit

class FieldNotInLayout(Exception): pass
class FieldValueNotSet(Exception): pass

#NOT_NULL_COLOR = gtk.gdk.color_parse('yellow')
NOT_NULL_COLOR = gtk.gdk.color_parse('LightGoldenrod')
FK_COLOR = gtk.gdk.color_parse('navyblue')
LBL_HOOVER_STYLE = gtk.gdk.color_parse('red')

class SqlMask (sqlwidget.SqlWidget):
    """doc string for sqlmask
    """

    __metaclass__ = dbg.LogTheMethods
    mwidgets = None  # mask widgets: key: field_name  value: ( gtkClass, widgetName )
    labels   = None  # correspondance Label <-> EventBox
#    map_record_n = 0  # number of the displayed record within mapper
    row_count = 0    # number of records in the mapper
    status = None
    current_idx = 0
####### Record browsing & saving
    def record_display(self, record=None, incr=0, index=None):
        """display an object record in the mask

        display the data provided by self.records[self.current + incr]
        incr: incr=incr 
        """
        if index:
            to_display = index
        else:
            to_display = self.current_idx + incr
        
        try:
            obj = self.records[to_display]
            self.current_idx = to_display
        except IndexError:
            if incr > 0:
                self.sb('Already last ' + msg_info)
            else:
                self.sb('Already first ' + msg_info)
            return None

        self.clear()
        msg_info = "record %s/%s" % (to_display , len(self.records))

        self.sb(msg_info)
        self.data_in = obj
        for field_name in self.field_list:
            try:
                self.set_value(field_name, getattr(obj, field_name))
                #self.get_value(field_name) ????
            except FieldNotInLayout, e:
                pass
        self.status = index

        self.sync()
        self.actions.on_record_display(new=obj)
        #sqlwidget.SqlWidget.record_display(self, new=data_in)
        
        ## return True if a record has beeen displayed. In case we 2 Mask in sync
        ## this will stop the master mask to continue in the next record until
        ## the first has been terminated
        #dbg.write("%s DATA DISPLAYed " % self.nick)
        return True
        
    def set_value(self, field_name, field_value):
        """this is the method that knows how to handle different type of data
        if field_name is a FKey ending with _id, it retrieves the description,
        shows it in the entry but stores the id in self.values[field_name]
        """
        #dbg.write("%s: %s" % (field_name, field_value))
        if field_name not in self.mwidgets:
            raise FieldNotInLayout("field_name: %s" % (field_name))

        widget = self.mwidgets[field_name]
        #print field_name, field_value
        if self.fields[field_name]['fkey'] and field_name.endswith('_id'):
            #if field_name == 'a_id':
            #    dbg.write("nick: %s - self.values[%s] = %s" % (self.nick, field_name, field_value))
            if field_value is None:
                try:
                    del self.values[field_name]
                except KeyError:
                    pass
            else:
                self.values[field_name] = field_value

            field_value = self.completion._lookup_value(field_name, field_value)

        #dbg.write( "name: %s type: %s" % ( field_name, self.fields[field_name] ))
        # Entry
        if isinstance (widget, gtk.Entry):
            if field_value == None:
                field_value = ''
            #dbg.write("widget.set_text( str(%s))" % field_value, field_name )
            widget.set_text( str(field_value) )
        # Dates
        elif isinstance (widget, dateedit.DateEdit):
            widget.set_property('time', field_value)


        # Text
        elif isinstance (widget, gtk.TextView):
            if field_value is None:
                field_value = ''
                
            buff = widget.get_buffer()
            buff.set_text( field_value)

        # Boolean
        elif self.fields[field_name]['type'] == bool:
            if not field_value :
#                 dbg.write("impongo false per %s che era '%s'" % (
#                     field_name, field_value))
                field_value = False
            widget.set_active(field_value)
            #dbg.write("%s: %s" % (field_value, widget.get_active()))

        else:
            raise FieldValueNotSet(
                "set_value does not know how to handle %s - (%s) and %s" % \
                (field_name, field_value, widget.__class__))
        
    def get_value(self, field_name, data=False, shown=False):
        """return the data for field_name
        in case self.values[field_name] exists, it gets that value instead

        data: boo - in case of a field not shown (es.: user_id) look for the value
              in self.data_in
        shown: If true the value is returned as is shown: ie: if an id is
               substituted by a lookup value, this latter value is returned
        """

        if field_name not in self.mwidgets:
            dbg.write("%s Non in mwidgets %s" % (field_name, self.mwidgets.keys()))
            if data:
                # print self.nick, "CHIESTO", field_name,"->", self.data_in[field_name]
                try:
                    #dbg.write('Soddisfatto con dati ingresso')
                    return self.data_in[field_name]
                
                except AttributeError, e:
                    
                    return 

            raise FieldNotInLayout("field_name: %s" % (field_name))

        widget = self.mwidgets[field_name]

        ## give a try if we have stored a value
        if shown is False:
            try:
                #dbg.write('Accontentato con values', self.values[field_name], self.values.keys())
                return self.values[field_name]
            except:
                pass
        
        # Entry
        if isinstance (widget, gtk.Entry):
            text = widget.get_text( )
            if text == '':
                if self.fields[field_name]['type'] in sqlwidget.NUMBERS:
                    return None
            return text

        # Text
        if isinstance (widget, gtk.TextView):
            buff = widget.get_buffer()
            ts = buff.get_iter_at_offset(0)
            te = buff.get_iter_at_offset(-1)
            text = buff.get_text(ts, te)
            #dbg.write(text)
            return text
        # Dates
        if isinstance (widget, dateedit.DateEdit):
            return widget.get_property('time')

        # Boolean
        elif self.fields[field_name]['type'] == bool:
            return widget.get_active( )
        return 
    
    def record_delete(self, widget=None, interactive=True):
        """invokes the validator before DELETing a record"""
        ## FIXME: validator
#        if self.sync_dict:
            
        if interactive:
            response = self.dialog(type='ok-cancel', text="Delete this record?")
            if response == gtk.RESPONSE_CANCEL:
                return

        self.session.delete(self.records[self.current_idx])
        #self.sqlData.delete()
        
        self.commit()
        self.clear() ## FIXME: is this necessary?
    
    def record_save(self, ev, constraint={}, *args):
        """invokes the validator before UPDATE/INSERT a record"""
        ## FIXME: validator
        
        #         if self.valid is not None:
        #             v = self.valid (self.table, record)
        #             v.validate ()

        if not self.status:
            self.record_save_new(None, constraint=constraint)
            return
    
        R = {}
        obj = self.records[self.currend_idx]
        for field_name in self.field_list:      
            try:
                value = self.get_value(field_name)
            except FieldNotInLayout:
                continue
            #dbg.write(field_name, value)
            
            t = self.fields[field_name]['type']
            #dbg.write("%s: - value: %r T: %s" % (field_name, value, t))
            if t == datetime.date:
                if value is not None:
                    value = t(value.year, value.month, value.day)
            elif t == datetime.datetime:
                if value is not None:
                    value = t(value.year, value.month, value.day,
                              value.hour, value.minute, value.second)
            else:
                if value is not None:
                    #dbg.write("value is", value)
                    value = t(value)

            if value != self.data_in[field_name]:
               if value == '' and self.data_in[field_name] == None:
                   pass
               else:
                   #dbg.write("%s: %r is not %r" % (field_name,
                   #                                value, self.data_in[field_name]))
                   #R[field_name] = value
                   setattr(obj, field_name, value)

##  FIXME: constraints
#         if R.keys():
#             R.update(self.constraint)
#             R.update(constraint)
#             dbg.write("CONSTRAINT:", R, constraint)
#             self.sqlData.set(R)

        self.commit()
        self.record_save_sync()
        
    def record_save_new(self, wdg, constraint={}):
        """Insert a new record
        """
        
        obj = self.get_new_object()
        for field_name in self.field_list:      
            try:
                value = self.get_value(field_name)
                #dbg.write('value: ', value)
            except FieldNotInLayout:
                continue
            
            t = self.fields[field_name]['type']
            if t == int and value == '':
                # skip type casting
                #setattr(obj, field_name, None)
                continue
            #dbg.write("%s: - value: %r t: %s" % (field_name, value, t))
            if t == datetime.date:
                #value = t(value.year, value.month, value.day)
                pass
            elif t == datetime.datetime:
                #value = t(value.year, value.month, value.day,
                #          value.hour, value.minute, value.second)
                pass
            else:
                if value is not None:
                    dbg.write("type of %s: %s" % (value, type(value)))
                    value = t(value)
                
            setattr(obj, field_name, value)


        obj = self.add_contraints(obj)
        self.actions.on_insert(obj)
        self.session.save(obj)
        self.status = obj
        dbg.write("self.status", self.status)

#         for z in self.sync_dict:
#             dbg.write('constraint', constraint)
#             z.record_save_new(None, constraint=constraint)

        self.commit ()
        self.record_save_sync()
        
        self.record_display()

        
    def clear(self, widget=None):
        """clear the mask for a new record"""
        self.status = None
        self.sb("New Record")
        
        for field_name in self.fields.keys():
            try:
                self.set_value(field_name, None)
            except FieldNotInLayout, e:
                pass
#        self.values.clear()

        ## sync
        for z in self.sync_dict:
            z.clear()
            z.sync_block()
        
    def record_new(self, widget=None):
        self.clear()
        
    def record_forward(self, ev):
        """display the next record in the mapper"""

        if self.sync_dict:
            ris = self.record_forward_sync(incr=1)
            #dbg.write('ris', ris)
            if ris:
                #dbg.write('esco')
                return
        
        return self.record_display(incr=1)
    
    def record_back(self, ev):
        """display the previous record in the mapper"""
        if self.sync_dict:
            ris = self.record_back_sync(incr=-1)
            #dbg.write('ris', ris)
            if ris:
                #dbg.write('esco')
                return
        
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
        self.clear()
        
    def record_save_cb(self,  accell_group, window, ord, flags):
        self.record_save(None)

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

        mwidgets: dict to store mask widgets { field_name : gtk_widget }
        also field that are not part of the table can be registered here
        (eg: a field that is ony filled by entry_completion)
                 
        """
        #dbg.show_caller()
        ## FIXME: does not work when renaming: euro.user_id -> euro_user_id

        ## mwidgets can be passed as argument of the class. In that case widgets
        ## used to represent the data are provided by another SqlMask
        if not self.mwidgets:
            self.mwidgets = {}
        ## by now I only use entry, date, radio and menu to represent data
        #dbg.dshow(self.w, 'e=')
#         if self.nick == 'art':
#             print self.w.keys()
        for field_name in self.fields.keys():
            #dbg.write(field_name)
            for mod in ('e','d','r','m','c', 'TX'):
                try:
                    widget = self.w["%s=%s" % (mod, field_name)]
                    self.mwidgets[field_name] = widget
                except:
                    pass
            # (gtkClass , gtkWidget)

        ## all EventBox 
        #dbg.write("self.w: %s" % self.w)
        #dbg.dshow(self.w, 'E=')
        self.labels = {}
        for field_name in self.fields.keys():
            lbl_name_wdg = "l=%s" % field_name
            if lbl_name_wdg in self.w:
                self.labels[field_name] = self.w[lbl_name_wdg]
                #dbg.write("%s -> %s"% (field_name, self.labels[field_name]))
            else:
                #dbg.write("Missing event_box for %s" % (field_name))
                pass
            
    def _add_colors_and_fonts(self):
        """add bg colors and fonts to signal needed fields"""

        for field_name in self.fields.keys():
            if field_name in self.mwidgets and self.fields[field_name]['edit']:
                if not self.fields[field_name]['nullable'] or \
                       self.fields[field_name]['pkey'] :
                    wdg = self.mwidgets[field_name]
                    #dbg.write(field_name)
                    wdg.modify_base(gtk.STATE_NORMAL, NOT_NULL_COLOR)

        for field_name in self.fields.keys():
            if field_name in self.labels:
                lbl    = self.labels[field_name]
                ev_wdg = self.labels[field_name].parent
                ## FIXME: is there a situation when I don't whant
                ##        blinking labels?
                if self.filter:
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
        
    def _add_constraints_and_connect(self):
        """Add controls according to data type represented
        check on input for integers
        configuring date / datetime for time*
        adding focus-out staff
        adding tooltips and click for filter_panel
        """
        for field_name in self.fields.keys():
            field_type = self.fields[field_name]['type']
            ## the widget may not be there, is layout has been provided
            ## as an argument
            if field_name not in self.mwidgets:
                #dbg.write("skip %s" % field_name)
                continue
            widget = self.mwidgets[field_name]
            if not widget:
                #dbg.write("Per campo: %s manca widget %s" %(field_name,widget))
                continue

            widget.set_property('sensitive', self.fields[field_name]['edit']) 
            # try:
#                 widget.set_property('editable', self.fields[field_name]['edit'])
#             except:
#                 widget.set_property('sensitive', self.fields[field_name]['edit']) 

            ## integer
            if field_type in sqlwidget.NUMBERS \
                   and not self.fields[field_name]['fkey']:
                # left justified
                #print "field_name:", field_name
                widget.set_alignment(1), widget
                # check the input
                widget.connect('key-press-event', self.digits_check_input_cb  )
                
            ## Strings
            if field_type == str or self.fields[field_name]['fkey']:
                #dbg.write("aggiungo <3> per %s" % (field_name))
                widget.connect('button-press-event',self.completion.pop_menu,
                               field_name, 3)
                widget.connect('key-press-event',
                               self.completion.keypress_event_cb,
                               field_name)
#                 widget.connect('key-press-event',
#                                self.completion.entry_short_cut_event,
#                                field_name)


#             else:
#                 dbg.write("fkey per %s: %s" %
#                          (field_name, self.fields[field_name]['fkey']))
            ## Dates / Datetime
            if field_type == datetime.date:
                widget.set_property('show-time', False)
            elif field_type == datetime.datetime:
                widget.set_property('show-time', True)
                
            #widget.connect('focus-out-event',self.focus_out__widget, field_name)
            #widget.connect('focus-in-event',self.focus_in__widget)
            try:
                widget.connect('activate',self.on_activate_cb, field_name)
            except:
                # FIX? dateedit don't have 'activate'
                pass

        ## add click that pops filter_panel
        if self.filter:
            for field_name, label in self.labels.iteritems():
                #print "label", label, 'field_name', field_name
                event_box = label.parent
                event_box.connect('button-press-event',
                                  self.filter_panel.add, field_name)

            

####### Validation
    def focus_out__widget(self, widget, event, field_name):
        self.last_visited_field = field_name
        #print "focus_out", event, field_name
        
    def focus_in__widget(self, widget, event, more=None):
        #print "focus_in"
        #print "more: ",more
        pass
    
    def on_activate_cb(self, widget, field_name):
        #print self.get_value(field_name)
        self.select()
    def select(self):
        pass
    

####### Misc
    def set_fkey_value(self, field_name, value):
        """needed for completion, to set real value when
        description is shown instead
        """
        self.values[field_name] = value
        
    def get_current_record(self):
        R = {}
        for field_name in self.field_list:
            try:
                R[field_name] = self.get_value(field_name)
            except FieldNotInLayout, e:
                #print "Field_notInLayout", e
                pass
        #dbg.write(R)
        return R
            

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
                                        lay=None,
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
            self.clear()
            
        return (lay, w)
    
    def get_mapper(self, mapper, tables):
        return self.dbproxy.get_mapper(mapper, tables[0])

    def parse_fields(self, fields):
        self.table_field_list = fields
        return SqlMask.parse_fields(self, None)
