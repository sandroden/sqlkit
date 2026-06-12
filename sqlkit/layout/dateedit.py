# Python GTK+ date and time entry widget. Version 0.2
# Copyright (C) 2005  Fabian Sturm, Sandro Dentella 2009
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

"""
.. _date_edit:

DateEdit
========

.. autoclass:: DateEdit
   :members: __init__, get_date, set_date

.. autoclass:: DateTimeEdit
   :members: __init__, get_datetime, set_datetime
   
"""


import sys
import os
import re
import time
import locale
import datetime

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from babel import dates

from sqlkit import _
# NB: css_utils is imported lazily inside the methods that need it to avoid a
# package import cycle (sqlkit.widgets.__init__ pulls SqlMask/SqlTable, which
# import sqlkit.layout while it is still initialising this very module).

class WrongDateFormat(Exception):
    pass
 # gnome_date_edit_new:
# @the_date: date and time to be displayed on the widget
# @show_time: whether time should be displayed
# @use_24_format: whether 24-hour format is desired for the time display.
#
# Description: Creates a new #GnomeDateEdit widget which can be used
# to provide an easy to use way for entering dates and times.
# If @the_date is 0 then current time is used.
#
 # Returns: a new #GnomeDateEdit widget.
class DateEdit(Gtk.Box):

    """
    basic gtk widget to edit data
    """
    __gtype_name__ = 'DateEdit'

    __gproperties__ = {
        'date': (GObject.TYPE_PYOBJECT,                       # type
                 'Date',                                    # nick name
                 'The date currently selected',             # description
                 GObject.PARAM_READWRITE),                  # flags

        'initial-date': (GObject.TYPE_PYOBJECT,
                         'Initial Date',
                         'The initial date',
                         GObject.PARAM_READABLE),

        'width-chars': (GObject.TYPE_PYOBJECT,
                        'Width of the entry in chars',
                        'The width of the entry',
                        GObject.PARAM_READWRITE),

    }

    __gsignals__ = {
        'date-changed': (GObject.SignalFlags.RUN_LAST, None,
                         ()),
    }

    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)

        # preset values
        self._initial_date = self._current_date = None
        self.invalid_date = False
        #datetime.datetime.today()

        try:
            self.locale_setup()
        except locale.Error:
            pass
        self.build_layout()

        hid = self._date_entry.connect('changed', self.date_entry_changed_cb)
        self._ids = {'date_entry_changed': (self._date_entry, hid)}
        self._date_button.connect('clicked', self.date_button_clicked_cb)

        self._calendar.connect('day-selected', self.day_selected_cb)
        self._calendar.connect('day-selected-double-click', self.day_selected_double_click_cb)

        self.date_format = 'short'
        self.date_parse = None
        self._id_timeout_add = None

    def locale_setup(self):
        if os.name == 'nt' or sys.platform == 'darwin':
            # Todo: fix this for windows
            self._use_24h_format = False
        else:
            # locale stuff, ugly hack, due to ugly locale functions
            saved_locale = locale.getlocale()
            if saved_locale[0] == None:
                # no locale set, so set it myself
                locale.setlocale(locale.LC_ALL, '')
            # the time format
            if locale.nl_langinfo(locale.T_FMT_AMPM) == '':
                self._use_24h_format = True
            else:
                self._use_24h_format = False
            # restore original locale
            locale.setlocale(locale.LC_ALL, saved_locale)

#####  layout
    def build_layout(self):

        self.set_spacing(6)
        date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(date_box)
        date_box.show()

        # the date entry
        self._date_entry = Gtk.Entry()
        self._entry = self._date_entry
        self._date_entry.set_max_length(15)
        self._date_entry.set_width_chars(10)
        # ex Gtk.Alignment.new(0, 0, 0, 0): no expand on either axis,
        # alignment to top-left. Applied directly to the entry.
        self._date_entry.set_halign(Gtk.Align.START)
        self._date_entry.set_valign(Gtk.Align.START)
        self._date_entry.set_hexpand(False)
        self._date_entry.set_vexpand(False)
        date_box.add(self._date_entry)
        date_box.child_set_property(self._date_entry, 'expand', False)
        self._date_entry.show()

        ## default style
        ctx = self._date_entry.get_style_context()
        self._default_base = ctx.get_background_color(Gtk.StateType.NORMAL)

        # the date button
        self._date_button = Gtk.Button()
        #pixmap = GdkPixbuf.Pixbuf.new_from_file('cal32.png')
        image = Gtk.Image()
        image.set_from_stock('sk-calendar', Gtk.IconSize.MENU)
        self._date_button.set_image(image)
        # ex Gtk.Alignment.new(0, 0, 0, 0): no expand on either axis,
        # alignment to top-left. Applied directly to the button.
        self._date_button.set_halign(Gtk.Align.START)
        self._date_button.set_valign(Gtk.Align.START)
        self._date_button.set_hexpand(False)
        self._date_button.set_vexpand(False)

        #self.pack_start(self._date_button, False, False, 0)
        date_box.add(self._date_button)
#         # the down arrow
#         arrow = Gtk.Arrow(Gtk.ArrowType.DOWN, Gtk.ShadowType.OUT)
#         self._date_button.add(arrow)
#         arrow.show()
        # finally show the button
        self._date_button.show()

        # the calendar popover (positioned automatically below the button by GTK;
        # on Wayland a Gtk.Window(POPUP) + move() is a no-op, Gtk.Popover is the
        # canonical replacement and natively handles ESC and click-outside).
        self._cal_popup = Gtk.Popover()
        self._cal_popup.set_relative_to(self._date_button)
        self._cal_popup.set_position(Gtk.PositionType.BOTTOM)
        self._cal_popup.set_tooltip_text(_(
            'Press Esc to close or double click a date to select it'))

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        self._cal_popup.add(frame)
        frame.show()

        # the calendar
        self._calendar = Gtk.Calendar()
        self._calendar.set_display_options(Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES
                                       # some space around the widgets, and two boxes
                                       | Gtk.CalendarDisplayOptions.SHOW_HEADING)
        frame.add(self._calendar)

        self._calendar.show()

    def flash_bg(self, entry, color, seconds):
        """
        flash background color for seconds to warn for wrong date format
        """
        from sqlkit.widgets.common import css_utils
        css_utils.set_background(entry, color)

        def _restore():
            css_utils.set_background(entry, self._default_base)
            return False

        GLib.timeout_add(1000 * seconds, _restore)

    def modify_base(self, state, color):
        """Set the date entry background (CSS).  ``color=None`` clears it.

        ``state`` is accepted for backward compatibility.  ``color`` may be a
        string or a :class:`Gdk.Color`.
        """
        from sqlkit.widgets.common import css_utils
        css_utils.set_background(self._date_entry, color)
        self._default_base = color

#####  callback
    def date_entry_changed_cb(self, entry):
        # check entry for valid date
        if self._id_timeout_add:
            GLib.source_remove(self._id_timeout_add)

        # let's delay the check so we can complete our input
        self._id_timeout_add = GLib.timeout_add(700, self.verify_date, entry)

    def verify_date(self, entry):
        """Verify the text anc heck if it parses as date, complain if not
        """
        # GLib stara' rimuovendo il source da solo (return False qui sotto):
        # azzero l'id ora, altrimenti al prossimo keystroke
        # date_entry_changed_cb chiamerebbe source_remove su un id morto.
        self._id_timeout_add = None
        date_string = self._date_entry.get_text()
        if not date_string:
            self.set_date(None)
            return False
        try:
            if callable(self.date_parse):
                the_date = self.date_parse(date_string)
            else:
                the_date = dates.parse_date(date_string)
        except Exception as e:
            self.wrong_date_format(e, date_string)
            return False

        try:
            self.set_date(the_date, from_focus_out=True)
        except Exception as e:
            print(e)
            return False
        from sqlkit.widgets.common import css_utils
        css_utils.set_background(entry, self._default_base)
        return False

    def date_button_clicked_cb(self, widget):
        # set calendar date
        if self.get_date():
            self._calendar.select_month(self._current_date.month - 1, self._current_date.year)
            self._calendar.select_day(self._current_date.day)

        # Gtk.Popover positions itself relative to the button (set in __init__);
        # ESC and click-outside are handled natively.
        self._cal_popup.popup()
        self._calendar.grab_focus()

    def day_selected_cb(self, widget):
        year, month, day = self._calendar.get_date()
        month += 1
        the_date = datetime.date(year, month, day)
        self.set_date(the_date)

    def day_selected_double_click_cb(self, widget, data=None):
        self._cal_popup.popdown()

####### date & gobject
    def wrong_date_format(self, error, date_string):
        self.invalid_date = True
        ctx = self._date_entry.get_style_context()
        provider = Gtk.CssProvider()
        provider.load_from_data('.entry { background: orangered; }')
        ctx.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        #self.flash_bg(self._date_entry, 'orangered', 2)

    def get_date(self):

        date_string = self._date_entry.get_text()

        if self.invalid_date:
            return date_string
            ## i'd like to raise the error but python wouldn't catch it...
            #raise WrongDateFormat(_('Wrong format for date %s' % date_string))

        if not date_string:
            self._current_date = None
            return None

        return self._current_date

    def set_date(self, new_date, from_focus_out=False):
        """
        new_date is a datetime.date object. Can be set by:
          - do_set_property
          - focus_out_event
          - popup click 
        """

        date_changed = not new_date == self._current_date
        self.invalid_date = False

        # set the time and date string
        entry, hid = self._ids['date_entry_changed']
        entry.handler_block(hid)

        if new_date:
            if callable(self.date_format):
                try:
                    self._date_entry.set_text(self.date_format(new_date))
                except:
                    self._date_entry.set_text(
                        dates.format_date(new_date, format='short'))
            else:
                self._date_entry.set_text(
                    dates.format_date(new_date, format=self.date_format))
        else:
            self._date_entry.set_text('')
        entry.handler_unblock(hid)

        if date_changed:
            self._current_date = new_date
            self.emit('date-changed')
            return True
        return False

    def do_get_property(self, property):
        if property.name == 'date':
            return self.get_date()
        elif property.name == 'initial-date':
            return self._initial_date
        elif property.name == 'width-chars':
            return self._date_entry.props.width_chars
        else:
            raise AttributeError('unknown property %s' % property.name)

    # set_properties
    def do_set_property(self, property, value):
        if property.name == 'date':
            self.set_date(value)
        elif property.name == 'width-chars':
            self._date_entry.props.width_chars = value
        else:
            raise AttributeError('unknown property %s' % property.name)


class DateTimeEdit(DateEdit):

    __gtype_name__ = 'DateTimeEdit'

    __gproperties__ = {
        'datetime': (GObject.TYPE_PYOBJECT,                       # type
                     'Date',                                    # nick name
                     'The date currently selected',             # description
                     GObject.PARAM_READWRITE),                  # flags

        'initial_datetime': (GObject.TYPE_PYOBJECT,
                             'Initial Date',
                             'The initial date',
                             GObject.PARAM_READABLE),

        'lower-hour': (GObject.TYPE_INT,
                       'Lower Hour',
                       'Lower hour in the time popup selector',
                       0,
                       24,
                       7,
                       GObject.PARAM_READWRITE),

        'upper-hour': (GObject.TYPE_INT,
                       'Upper Hour',
                       'Upper hour in the time popup selector',
                       0,
                       24,
                       19,
                       GObject.PARAM_READWRITE),

        'show-time': (GObject.TYPE_BOOLEAN,
                      'Show Time',
                      'Show the time widget',
                      True,
                      GObject.PARAM_READWRITE),

        'use-24h-format': (GObject.TYPE_BOOLEAN,
                           'Use 24h Format',
                           'Display time in 24h format',
                           True,
                           GObject.PARAM_READWRITE)
    }

    __gsignals__ = {
        'datetime-changed': (GObject.SignalFlags.RUN_LAST, None,
                             ()),
        'time-changed': (GObject.SignalFlags.RUN_LAST, None,
                         ()),
    }

    def __init__(self):

        # preset values
        self._initial_datetime = self._current_datetime = None
        self._lower_hour = 7
        self._upper_hour = 19
        self._show_time = True
        self._use_24h_format = True

        DateEdit.__init__(self)
        self._time_combobox.connect('changed', self.time_combobox_changed_cb)
        self._time_combobox.get_child().connect('focus-out-event', self.time_entry_focus_out_event_cb)
        self.connect('realize', self.fill_time_combobox)

    def build_layout(self):

        DateEdit.build_layout(self)

        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(time_box)
        time_box.show()

        # the time entry combobox: GTK3 dropped Gtk.ComboBoxEntry, the
        # equivalent is a Gtk.ComboBox built with the has-entry property
        # (Gtk.ComboBox.new_with_entry()).
        self._time_combobox = Gtk.ComboBox.new_with_entry()
        self._time_combobox.get_child().set_max_length(12)
        self._time_combobox.get_child().set_width_chars(8)
        time_box.add(self._time_combobox)
        self._time_combobox.set_no_show_all(True)
        self._time_combobox.show()

        # set the initial widget properties
        self.set_show_time(self._show_time)
        self.set_use_24h_format(self._use_24h_format)

    def fill_time_combobox(self, widget, data=None):
        if self._lower_hour > self._upper_hour:
            return

        # create the new model
        store = Gtk.TreeStore(str)
        for i in range(self._lower_hour, self._upper_hour + 1):
            label = self._format_time_label(i, 0)
            iter = store.append(None, [label])

            # create sub menu
            for j in range(15, 60, 15):
                store.append(iter, [self._format_time_label(i, j)])

        # finally replace current model with this new one
        self._time_combobox.set_model(store)
        # On a GTK3 has-entry combobox the API is [get|set]_entry_text_column;
        # the GTK2 GtkComboBoxEntry [get|set]_text_column was renamed.
        if self._time_combobox.get_entry_text_column() == -1:
            self._time_combobox.set_entry_text_column(0)

    def _format_time_label(self, hour, minute):
        # AM/PM rendered explicitly: strftime('%p') follows the C locale and
        # is empty in many EU locales (e.g. it_IT), which would collapse 12h
        # labels to ambiguous "01:00", "02:00", ...
        if self._use_24h_format:
            return '%02d:%02d' % (hour, minute)
        suffix = 'AM' if hour < 12 else 'PM'
        display_h = ((hour - 1) % 12) + 1
        return '%02d:%02d %s' % (display_h, minute, suffix)

    def _parse_time_text(self, time_text):
        # Accept 'HH:MM', 'HH:MM AM/PM' (any case, optional space).
        m = re.match(r'^\s*(\d{1,2})[:.](\d{2})\s*([AaPp][Mm])?\s*$', time_text)
        if not m:
            raise ValueError('invalid time: %r' % time_text)
        hour, minute = int(m.group(1)), int(m.group(2))
        suffix = m.group(3)
        if suffix:
            suffix = suffix.upper()
            if not 1 <= hour <= 12:
                raise ValueError('invalid 12h hour: %d' % hour)
            if suffix == 'AM':
                hour = 0 if hour == 12 else hour
            else:
                hour = 12 if hour == 12 else hour + 12
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError('out of range: %02d:%02d' % (hour, minute))
        return datetime.time(hour, minute)

    def time_combobox_changed_cb(self, widget, data=None):
        # if the changed was due to a time selection in the menu,
        # handle as if focus-out-event
        if self._time_combobox.get_active_iter() != None:
            self.time_entry_focus_out_event_cb(widget, data)

    def time_entry_focus_out_event_cb(self, widget, data=None):

        # check entry for valid time, reset if not
        time_text = self._time_combobox.get_child().get_text()
        try:
            the_time = self._parse_time_text(time_text)
        except Exception as e:
            self.wrong_time_format(e, time_text)
            return
        self.set_time(the_time)

    ############################################
    # properties and their convenience functions

    def wrong_time_format(self, error, date_string):
        self.invalid_time = True
        self.flash_bg(self._time_combobox.get_child(), 'orangered', 2)

    def set_use_24h_format(self, use_24h_format):
        dt = self.get_time()
        self._use_24h_format = use_24h_format
        self.fill_time_combobox(self)
        self._current_time = dt

    # get_properties
    def set_lower_hour(self, value):
        if value < 0 or value > 24 or value > self._upper_hour:
            return
        self._lower_hour = value
        self.fill_time_combobox(None)

    def set_upper_hour(self, value):
        if value < 0 or value > 24 or value < self._lower_hour:
            return
        self._upper_hour = value
        self.fill_time_combobox(None)

    def set_show_time(self, show_time):
        if show_time == True:
            self._show_time = True
            self._time_combobox.show()
        else:
            self._show_time = False
            self._time_combobox.hide()

    def get_time(self):
        """
        return only the time
        """

        time_string = self._time_combobox.get_child().get_text()

        if not time_string:
            self._current_time = None
            return None

        else:
            try:
                return self._parse_time_text(time_string)
            except Exception as e:
                self.wrong_time_format(e, time_string)
                return time_string

    def get_datetime(self):
        ### I should propagate errors via an Exception but I'm not able write now. See:
        # http://www.mail-archive.com/pygtk@daa.com.au/msg17444.html

        new_date = self.get_date()
        if isinstance(new_date, str):
            return new_date

        new_time = self.get_time()
        if isinstance(new_time, str):
            return new_time

        if not new_date:
            return None

        return datetime.datetime.combine(self.get_date(), self.get_time() or datetime.time())

    def set_datetime(self, new_datetime):

        if new_datetime:
            date_changed = self.set_date(new_datetime.date())
            time_changed = self.set_time(new_datetime.time())
        else:
            date_changed = self.set_date(None)
            time_changed = self.set_time(None)

        if date_changed or time_changed:
            self.invalid_time = False
            self.invalid_date = False
            self.emit('datetime-changed')

    def set_time(self, new_time, focus=False):

        time_changed = not new_time == self._current_time
        if new_time == None:
            self._time_combobox.get_child().set_text('')
        else:
            # set the time and date string
            if self._use_24h_format == True:
                self._time_combobox.get_child().set_text(new_time.strftime('%H:%M'))
            else:
                self._time_combobox.get_child().set_text(new_time.strftime('%I:%M %p'))

        # emit signal on time change
        if time_changed == True:
            self._current_time = new_time
            self.invalid_time = False
            self.emit('time-changed')
            return True

        return False

    # get_properties
    def do_get_property(self, property):
        if property.name == 'datetime':
            return self.get_datetime()
        elif property.name == 'initial-datetime':
            return self._initial_datetime
        elif property.name == 'lower-hour':
            return self._lower_hour
        elif property.name == 'upper-hour':
            return self._upper_hour
        elif property.name == 'show-time':
            return self._show_time
        elif property.name == 'use-24h-format':
            return self._use_24h_format
        else:
            raise AttributeError('unknown property %s' % property.name)

    # set_properties
    def do_set_property(self, property, value):
        if property.name == 'datetime':
            self.set_datetime(value)
        elif property.name == 'lower-hour':
            self.set_lower_hour(value)
        elif property.name == 'upper-hour':
            self.set_upper_hour(value)
        elif property.name == 'show-time':
            self.set_show_time(value)
        elif property.name == 'use-24h-format':
            self.set_use_24h_format(value)
        else:
            raise AttributeError('unknown property %s' % property.name)


class EntryCal(Gtk.Entry):

    """
    basic gtk widget to edit data that uses primary/secondary icon stock
    """
    __gtype_name__ = 'DateEdit2'

    __gproperties__ = {
        'date': (GObject.TYPE_PYOBJECT,                       # type
                 'Date',                                    # nick name
                 'The date currently selected',             # description
                 GObject.PARAM_READWRITE),                  # flags

        'initial-date': (GObject.TYPE_PYOBJECT,
                         'Initial Date',
                         'The initial date',
                         GObject.PARAM_READABLE),

        'width-chars': (GObject.TYPE_PYOBJECT,
                        'Width of the entry in chars',
                        'The width of the entry',
                        GObject.PARAM_READWRITE),

    }

    __gsignals__ = {
        'date-changed': (GObject.SignalFlags.RUN_LAST, None,
                         ()),
    }

    def __init__(self):

        GObject.GObject.__init__(self)
        self.props.primary_icon_stock = 'gtk-quit'
        self.props.secondary_icon_stock = 'sk-calendar'
        self.props.secondary_icon_tooltip_text = "Calendar"

if __name__ == '__main__':

    from . import misc  # adds the sk-calendar stock-icon
    w = Gtk.Window()
    d = EntryCal()
#    d = DateTimeEdit()
    w.add(d)
    w.show_all()

    Gtk.set_interactive(True)
