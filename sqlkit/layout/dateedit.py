# Python GTK+ date and time entry widget. Version 0.2
# Copyright (C) 2005  Fabian Sturm
#
# ported from the libgnomeui/gnome-dateedit.c
# with changes where it makes sense for python (e.g. constructor, 
# return types etc.)
#
# This widget is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this widget; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

# Todo:
#
# mnemonic stuff
# gobject register no longer needed...


import sys
import os
import time
import locale
import datetime

import pygtk
#pygtk.require('2.0')
import gobject
import gtk
from gtk import gdk
 
 # gnome_date_edit_new:
 # @the_time: date and time to be displayed on the widget
 # @show_time: whether time should be displayed
 # @use_24_format: whether 24-hour format is desired for the time display.
 #
 # Description: Creates a new #GnomeDateEdit widget which can be used
 # to provide an easy to use way for entering dates and times.
 # If @the_time is 0 then current time is used.
 #
 # Returns: a new #GnomeDateEdit widget. 
class DateEdit(gtk.HBox):
    __gtype_name__ = 'DateEdit'
    
    __gproperties__ = {
        'time' : (gobject.TYPE_PYOBJECT,                       # type
                    'Time',                                    # nick name
                    'The time currently selected',             # description
                    gobject.PARAM_READWRITE),                  # flags

        'initial_time' : (gobject.TYPE_PYOBJECT,
                    'Initial Time',
                    'The initial time',
                    gobject.PARAM_READABLE),
                  
        'lower_hour' : (gobject.TYPE_INT,
                    'Lower Hour',
                    'Lower hour in the time popup selector',
                    0,
                    24,
                    7,
                    gobject.PARAM_READWRITE),

        'upper_hour' : (gobject.TYPE_INT,
                    'Upper Hour',
                    'Upper hour in the time popup selector',
                    0,
                    24,
                    19,
                    gobject.PARAM_READWRITE),
                  
        'show_time' : (gobject.TYPE_BOOLEAN,
                    'Show Time',
                    'Show the time widget',
                    True,
                    gobject.PARAM_READWRITE),
                    
        'use_24h_format' : (gobject.TYPE_BOOLEAN,
                    'Use 24h Format',
                    'Display time in 24h format',
                    True,
                    gobject.PARAM_READWRITE)
    }

    __gsignals__ = {
        'time_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          ()),
        'date_changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          ()),                          
        'wrong-date-format' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          (gobject.TYPE_STRING)),                          
    
        'good-date-format' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                          ()),                          
    
    }

    def __init__(self):
        gtk.HBox.__init__(self)
        
        # preset values
        self.__initial_time = self.__current_time = None
        #datetime.datetime.today()
        self.__lower_hour = 7;
        self.__upper_hour = 19;        
        self.__show_time = True
        
        if os.name == 'nt':
            # Todo: fix this for windows
            self.__use_24h_format = False
        else:
            # locale stuff, ugly hack, due to ugly locale functions
            saved_locale = locale.getlocale()
            if saved_locale[0] == None:
                # no locale set, so set it myself
                locale.setlocale(locale.LC_ALL, '')
            # the time format
            if locale.nl_langinfo(locale.T_FMT_AMPM) == '' :
                self.__use_24h_format = True
            else:
                self.__use_24h_format = False
            # restore original locale
            locale.setlocale(locale.LC_ALL, saved_locale)
        
        # some space around the widgets, and two boxes
        self.set_spacing(6)
        date_box = gtk.HBox()
        self.add(date_box)
        date_box.show()
        time_box = gtk.HBox()
        self.add(time_box)
        time_box.show()
        
        # the date entry
        self.__date_entry = gtk.Entry()
        self.__date_entry.connect('focus-out-event', self.date_entry_focus_out_event)
        self.__date_entry.set_max_length(15)
        self.__date_entry.set_width_chars(10)
        self.__align_entry = gtk.Alignment(1,0,1,0)
        #self.pack_start(self.__date_entry, True, True, 0)
        date_box.add(self.__align_entry)
        self.__align_entry.add(self.__date_entry)
        self.__align_entry.show()
        self.__date_entry.show()
        
        # the date button
        self.__date_button = gtk.Button()
        self.__align_arrow = gtk.Alignment(0,0,0,0)
        self.__align_arrow.show()
        self.__align_arrow.add(self.__date_button)

        self.__date_button.connect('clicked', self.date_button_clicked)
        #self.pack_start(self.__date_button, False, False, 0)
        date_box.add(self.__align_arrow)
        # the down arrow
        arrow = gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_OUT)
        self.__date_button.add(arrow)
        arrow.show()
        # finally show the button
        self.__date_button.show()
        
        # the time entry combobox
        self.__time_combobox = gtk.ComboBoxEntry()
        self.__time_combobox.connect('changed', self.time_combobox_changed)
        self.__time_combobox.child.connect('focus-out-event', self.time_entry_focus_out_event)
        self.__time_combobox.child.set_max_length(12)
        self.__time_combobox.child.set_width_chars(8)
        time_box.add(self.__time_combobox)
        self.__time_combobox.set_no_show_all(True)
        self.__time_combobox.show()
        self.connect('realize', self.fill_time_combobox)
        
        # the calendar popup
        self.__cal_popup = gtk.Window(gtk.WINDOW_POPUP)
        self.__cal_popup.set_title('popup for calendar')
        self.__cal_popup.set_events(self.__cal_popup.get_events() | gdk.KEY_PRESS_MASK)
        self.__cal_popup.connect('delete_event', self.delete_popup)
        self.__cal_popup.connect('key_press_event', self.key_press_popup)
        self.__cal_popup.connect('button_press_event', self.button_press_popup)
        self.__cal_popup.set_resizable(False) # Todo: Needed?
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)
        self.__cal_popup.add(frame)
        frame.show()
        # the calendar
        self.__calendar = gtk.Calendar()
        self.__calendar.display_options(gtk.CALENDAR_SHOW_DAY_NAMES 
                                        | gtk.CALENDAR_SHOW_HEADING)
        self.__calendar.connect('day-selected', self.day_selected)
        self.__calendar.connect('day-selected-double-click', self.day_selected_double_click)
        frame.add(self.__calendar)
        self.__calendar.show()
           
        # set the initial widget properties
        self.set_show_time(self.__show_time)
        self.set_time(self.__initial_time)
        self.set_use_24h_format(self.__use_24h_format)
        self.date_format = '%x'

    def popup_grab_on_window(self, window, activate_time):
        if gdk.pointer_grab(window, True, gdk.BUTTON_PRESS_MASK 
                                          | gdk.BUTTON_RELEASE_MASK
                                          | gdk.POINTER_MOTION_MASK, 
                            None, None, activate_time) == 0:
                if gdk.keyboard_grab (window, True, activate_time) == 0:
                    return True
                else:
                    gdk.pointer_ungrab(activate_time)
                    return False
        return False


    def position_popup(self):
        req = self.__cal_popup.size_request()
        (x,y) = gdk.Window.get_origin(self.__date_button.window)

        x += self.__date_button.allocation.x
        y += self.__date_button.allocation.y
        bwidth = self.__date_button.allocation.width
        bheight = self.__date_button.allocation.height

        x += bwidth - req[0]
        y += bheight

        if x < 0: x = 0
        if y < 0: y = 0
        
        self.__cal_popup.move(x,y)


    def hide_popup(self):
        self.__cal_popup.hide()
        self.__cal_popup.grab_remove()
        
        
    def date_entry_focus_out_event(self, widget, data=None):
        # check entry for valid date, reset if not
        string = self.__date_entry.get_text()
        if string is '':
            self.set_time(None)
            return
        try:
            new_date = time.strptime(string, self.date_format)
            if self.__show_time:
                the_time = datetime.datetime(new_date.tm_year,
                                             new_date.tm_mon,
                                             new_date.tm_mday,
                                             self.__current_time.hour,
                                             self.__current_time.minute,
                                             self.__current_time.second)
            else:
                the_time = datetime.datetime(new_date.tm_year,
                                             new_date.tm_mon,
                                             new_date.tm_mday,
                                             )
            self.set_time(the_time)
        except ValueError, e:
            self.emit('wrong-date-format', string)
            self.set_time(self.__current_time)
 
 
    def date_button_clicked(self, widget, data=None):
        # Temporarily grab pointer and keyboard on a window we know exists        
        if not self.popup_grab_on_window(widget.window, gtk.get_current_event_time()):
            print 'error during grab'
            return
        
        # set calendar date
        if not self.get_time:
            self.__calendar.select_month(self.__current_time.month - 1, self.__current_time.year)
            self.__calendar.select_day(self.__current_time.day)        
        
        # position and show popup window
        self.position_popup()
        self.__cal_popup.grab_add()
        self.__cal_popup.show()
        self.__calendar.grab_focus()
        
        # Now transfer our grabs to the popup window, this should always succed
        self.popup_grab_on_window(self.__cal_popup.window, gtk.get_current_event_time())


    def day_selected(self, widget, data=None):
        (year, month, day) = self.__calendar.get_date()
        month += 1        
        try:
            the_time = datetime.datetime(year, month, day,
                                         self.__current_time.hour,
                                         self.__current_time.minute,
                                         self.__current_time.second)
        except:
            the_time = datetime.datetime(year, month, day,0,0,0)
        self.set_time(the_time)


    def day_selected_double_click(self, widget, data=None):
        self.hide_popup()


    def key_press_popup(self, widget, data=None):        
        # Todo, Fixme: what is the name of gdk.Escape? missing?
        if data == None or data.keyval != 65307:
            return False

        # Todo: does not work and what does it do anyway?
        #widget.stop_emission_by_name('key_press_event')
        self.hide_popup()
        return True


    # Todo: is this correct?
    def button_press_popup(self, widget, data=None):
        # We don't ask for button press events on the grab widget, so
        # if an event is reported directly to the grab widget, it must
        # be on a window outside the application (and thus we remove
        # the popup window). Otherwise, we check if the widget is a child
        # of the grab widget, and only remove the popup window if it
        # is not.
        if data == None or data.window == None:
            return False
            
        child = data.window.get_user_data()
        if child != widget:
            while child:
                if child == widget:
                    return False
                child = child.parent
                
        self.hide_popup()
        return True


    def delete_popup(self, widget, data=None):
        # Todo: is this ever called??
        print 'delete_popup'
        self.hide_popup();
        return TRUE;


    def fill_time_combobox(self, widget, data=None):
        if self.__lower_hour > self.__upper_hour:
            return
            
        # create the new model    
        store = gtk.TreeStore(str)
        for i in range(self.__lower_hour, self.__upper_hour + 1):
            the_time = datetime.time(i, 0)
            if self.__use_24h_format:
                label = the_time.strftime('%H:%M')
            else:
                label = the_time.strftime('%I:%M %p')
            iter = store.append(None, [label])
            
            # create sub menu
            for j in range(15,60,15):
                the_time = datetime.time(i,j)
                if self.__use_24h_format:
                    label = the_time.strftime('%H:%M')
                else:
                    label = the_time.strftime('%I:%M %p')
                store.append(iter, [label])
                
        # finally replace current model with this new one                
        self.__time_combobox.set_model(store)
        if self.__time_combobox.get_text_column() == -1:
            self.__time_combobox.set_text_column(0)


    def time_combobox_changed(self, widget, data=None):
        # if the changed was due to a time selection in the menu, 
        # handle as if focus-out-event
        if self.__time_combobox.get_active_iter() != None:
            self.time_entry_focus_out_event(widget, data)

        
        
    def time_entry_focus_out_event(self, widget, data=None):

        # check entry for valid time, reset if not
        str = self.__time_combobox.child.get_text()
        try:
            if self.__use_24h_format:
                new_time = time.strptime(str, '%H:%M')
            else:
                new_time = time.strptime(str, '%I:%M %p')

            the_time = datetime.datetime(self.__current_time.year,
                                         self.__current_time.month,
                                         self.__current_time.day,
                                         new_time.tm_hour,
                                         new_time.tm_min,
                                         self.__current_time.second)
            self.set_time(the_time)
        except ValueError:
            self.set_time(self.__current_time)
        
        
        
    ############################################
    # properties and their convenience functions

    def get_time(self):
        if self.__show_time:
            if self.__time_combobox.child.get_text() == '':
                self.__current_time = None
                    
            return self.__current_time
        else:
            if self.__date_entry.get_text() == '':
                self.__current_time = None
                    
            if self.__current_time is None:
                return None
            else:
                the_time = datetime.date(self.__current_time.year,
                                         self.__current_time.month,
                                         self.__current_time.day,
                                         )
            return the_time


    def set_time(self, the_time):
        # check for valid datetime
        if the_time is None or the_time  == '':
            #the_time = datetime.datetime.today()
            if self.__current_time == None:
                date_changed = False
            else:
                date_changed = True
                self.__current_time = None
                self.__date_entry.set_text('')
                self.emit('date-changed')    
                
            if self.__current_time == None:
                time_changed = False
            else:
                time_changed = True
                self.__time_combobox.child.set_text('')
                self.emit('time-changed')
            return
        #assert isinstance(the_time, (datetime.datetime, datetime.date, datetime.time))

        # convert a date/time to full datetime
        if not isinstance(the_time, datetime.datetime):
            if isinstance(the_time, datetime.date):
                try:
                    the_time = datetime.datetime(the_time.year,
                                                 the_time.month,
                                                 the_time.day,
                                                 self.__current_time.hour,
                                                 self.__current_time.minute,
                                                 self.__current_time.second)
                except:
                    the_time = datetime.datetime(the_time.year,
                                                 the_time.month,
                                                 the_time.day,
                                                 0, 0, 0)
                    
            elif isinstance(the_time, datetime.time):
                try:
                    the_time = datetime.datetime(self.__current_time.year,
                                                 self.__current_time.month,
                                                 self.__current_time.day,
                                                 the_time.hour,
                                                 the_time.minute,
                                                 the_time.second)
                except:
                    the_time = datetime.datetime(0,0,0,
                                                 the_time.hour,
                                                 the_time.minute,
                                                 the_time.second)

        # conditional vars
        date_changed = False
        time_changed = False

        # check if time not yet set
        if self.__current_time == None:
            self.__current_time = the_time
        
        # check if date changed
        if self.__current_time.day != the_time.day or \
           self.__current_time.month != the_time.month or \
           self.__current_time.year != the_time.year:
            date_changed = True
            
        # check if time chanegd
        if self.__current_time.hour != the_time.hour or \
           self.__current_time.minute != the_time.minute or \
           self.__current_time.second != the_time.second:
            time_changed = True       
        
        # now we can override the old time with the new one
        self.__current_time = the_time

        # set the time and date string
        self.__date_entry.set_text(the_time.strftime(self.date_format))
        if self.__use_24h_format == True:
            self.__time_combobox.child.set_text(the_time.strftime('%H:%M'))
        else:
            self.__time_combobox.child.set_text(the_time.strftime('%I:%M %p'))

        # emit signal on date change
        if date_changed == True:
            self.emit('date-changed')
            
        # emit signal on time change
        if time_changed == True:
            self.emit('time-changed')    
       

    def set_lower_hour(self, value):
        if value < 0 or value > 24 or value > self.__upper_hour:
            return
        self.__lower_hour = value
        self.fill_time_combobox(None)


    def set_upper_hour(self, value):
        if value < 0 or value > 24 or value < self.__lower_hour:
            return
        self.__upper_hour = value
        self.fill_time_combobox(None)
        
        
    def set_show_time(self, show_time):
        if show_time == True:
            self.__show_time = True
            self.__time_combobox.show()
        else:
            self.__show_time = False
            self.__time_combobox.hide()
    
    
    def set_use_24h_format(self, use_24h_format):
        dt = self.get_time()
        self.__use_24h_format = use_24h_format
        self.fill_time_combobox(self)
        self.set_time(dt)


    # get_properties
    def do_get_property(self, property): 
        if property.name == 'time':
            return self.get_time()
        elif property.name == 'initial-time':
            return self.__initial_time
        elif property.name == 'lower-hour': 
            return self.__lower_hour
        elif property.name == 'upper-hour':
            return self.__upper_hour
        elif property.name == 'show-time':
            return self.__show_time
        elif property.name == 'use-24h-format':
            return self.__use_24h_format
        else:
            raise AttributeError, 'unknown property %s' % property.name


    # set_properties
    def do_set_property(self, property, value):
        if property.name == 'time':
            self.set_time(value)
        elif property.name == 'lower-hour': 
            self.set_lower_hour(value)
        elif property.name == 'upper-hour':
            self.set_upper_hour(value)
        elif property.name == 'show-time':
            self.set_show_time(value)
        elif property.name == 'use-24h-format':
            self.set_use_24h_format(value)
        else:
            raise AttributeError, 'unknown property %s' % property.name
            
    def modify_base(self, state, color):
        self.__date_entry.modify_base(state, color)
        self.__time_combobox.get_children()[0].modify_base(state, color)
        

# finally register our new Type
if gobject.pygtk_version < (2, 8):
	    gobject.type_register(DateEdit)

