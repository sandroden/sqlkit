from datetime import datetime

from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Pango

from sqlkit import debug as dbg
from .multiline_cell import MultilineCellRenderer

class CellEditableCalendar(Gtk.TextView, Gtk.CellEditable):

    """An editable that allows to edit dates via a calendar popup
    Can also edit datetime but the popup will just change the date, not allow
    to edit the time
    """

    __gproperties__ = {
        'editing-canceled': (GObject.TYPE_BOOLEAN,                        # type
                             'editing canceled',                         # nick name
                             # description
                             'Indicates whether editing on the cell has been canceled.',
                             False,                                        # default value
                             GObject.PARAM_READWRITE)                   # flags
    }

    datetime = None

    def __init__(self, datetime, pos=None, wdg=None, cell_area=None, fmt_func=None):

        self.datetime = datetime
        self.fmt_func = fmt_func
        GObject.GObject.__init__(self)
        #self.set_has_window(False)
        self.cal = Gtk.Calendar()
        #self.cal.show()
        self.cal.select_month(self.datetime.month - 1, self.datetime.year)
        self.cal.select_day(self.datetime.day)
        self.w = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.set_editable(True)
        self.w.add(self.cal)
        #self.w.connect("delete_event", self.delete_event)
        self.cal.connect("day-selected-double-click", self.delete_event)
        self.cal.connect("event", self.cal_event)
        self.position_popup(wdg, self.w, cell_area)
        self.show_all()
        self.grab_focus()
        self.w.show_all()
        self.connect('key-press-event', self.keypress_event)

    def position_popup(self, widget, popup, ca):
        # the get_origin method returns  the origin comprising the headers
        # the get_cell _area don't!!! (so I add cell_height doing 2*...))

        # you need child to show_all() to get the dimentions correctly
        child = popup.get_children()[0]
        child.show_all()

        req = popup.size_request()
        popup_width, popup_height = req.width, req.height
        # GTK3's Gdk.Window.get_origin() returns (ok, x, y) — a 3-tuple — while
        # the GTK2/PyGTK API returned just (x, y).  pygi-convert.sh renamed the
        # call but left the 2-value unpacking, which raised ValueError when the
        # calendar popup opened.  Unpack the leading success flag explicitly.
        _ok, x, y = Gdk.Window.get_origin(widget.get_window())

        # path, col, x1, y1 = widget.get_path_at_pos(event.x, event.y)
        # ca = widget.get_cell_area(path, col)

        X = x + ca.x
        Y = y + ca.y + 2*ca.height + 4

        # border case: the cell is too close to the border to allow the window
        # I don't want the mouse to be over the popup since an undesired click
        # would change the date... Use the Monitor API (Gdk.Screen.* deprecated
        # since GTK 3.22).
        _display = Gdk.Display.get_default()
        _monitor = _display.get_primary_monitor() or _display.get_monitor(0)
        _geom = _monitor.get_geometry()
        if Y + popup_height > _geom.height:
            Y = y + ca.y + ca.height - popup_height
        if X + popup_width > _geom.width:
            X = _geom.width - popup_width

        popup.move(X, Y)

    def keypress_event(self, w, event):
        accelname = Gtk.accelerator_name(event.keyval, event.get_state())
        if accelname == 'Delete':
            self.date = None
            self.emit('editing-done')
            return True

        return False

    def cal_event(self, w, e):
        text = self.fmt_func(self.get_calendar_date())
        #text = self.get_calendar_date().strftime("%d/%m/%y")

        tb = self.get_buffer()
        tb.set_text(text)
        return False

    def do_start_editing(self, event):
        pass

    def do_remove_widget(self):
        pass

    def do_stop_editing(self):

        self.w.destroy()
        self.destroy()

    def do_editing_done(self):
        self.w.destroy()
        self.destroy()
        pass

    def delete_event(self, w=None, e=None):

        date = self.get_calendar_date()
        try:
            ## in case self.datetime is a date, we preserve the time
            self.datetime = datetime.combine(date, self.datetime.time())
        except Exception as e:
            ## self.datetime may just be a date...
            self.datetime = date

        self.emit('editing-done')
        self.w.destroy()
        self.destroy()
        return True

    def get_calendar_date(self):
        """calendare return a tuple: genuary is 0!"""

        calendar_tuple = list(self.cal.get_date())
        calendar_tuple[1] += 1
        return datetime(*tuple(calendar_tuple))


GObject.type_register(CellEditableCalendar)

class CellRendererDate(Gtk.CellRenderer):
    date = None
##     editable = None

    __gproperties__ = {
        'date': (GObject.TYPE_PYOBJECT,
                 'date of cell',
                 'date object contained in cell',
                 GObject.PARAM_READWRITE)
    }

    __gsignals__ = {
        'date-changed': (GObject.SignalFlags.RUN_FIRST, None,
                         (GObject.TYPE_STRING, GObject.TYPE_PYOBJECT)
                         )
    }

    def __init__(self, master=None, field_name=None, *args, **kwargs):
        GObject.GObject.__init__(self)
        #dbg.write()
        self.date = None
        self.master = master
        self.field_name = field_name

        #return Gtk.CellRenderer.__gobject_init__(self, *args, **kwargs)

    def do_pango_layout(self, widget):
        pc = widget.get_pango_context()
        pl = Pango.Layout(pc)
        pl.set_text(self.date_formatter(self.date))
        return pl

    def do_get_size(self, widget, cell_area):

        #dbg.show_caller()
        xpad = self.get_property('xpad')
        ypad = self.get_property('ypad')

        xalign = self.get_property('xalign')
        yalign = self.get_property('yalign')

        layout = self.do_pango_layout(widget)
        width, height = layout.get_pixel_size()

        x_offset = xpad
        y_offset = ypad

        if cell_area:

            x_offset = xalign * (cell_area.width - width)
            x_offset = max(x_offset, xpad)
            x_offset = int(round(x_offset, 0))

            y_offset = yalign * (cell_area.height - height)
            y_offset = max(y_offset, ypad)
            y_offset = int(round(y_offset, 0))

        width = width + (xpad * 2)
        height = height + (ypad * 2)

        return x_offset, y_offset, width, height

    def date_formatter(self, date):
        if date is None:
            return ""
        return self.master.gui_fields[self.field_name].format_value(date)
        #return date.strftime("%d/%m/%y")

    def do_start_editing(self, event, widget, path, background_area,
                         cell_area, flags):

        if self.date is None:
            date = datetime.now()
        else:
            date = self.date
        #dbg.ddir(cell_area)
        ce = CellEditableCalendar(datetime=date, cell_area=cell_area,
                                  wdg=widget,
                                  fmt_func=self.master.gui_fields[self.field_name].format_value)
#        ce = CellEditableCalendar(date = date, pos=(event.x, event.y))
        ce.show()
        ce.grab_focus()
        ce.connect('editing-done', self.editing_done, widget, path)

        return ce

    def editing_done(self, widget, treeview, path):

        self.stop_editing(True)
        self.emit('date-changed', path, widget.datetime)
        return True

    def do_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):

        x_offset, y_offset, width, height = self.do_get_size(widget, cell_area)
        pl = self.do_pango_layout(widget)
        widget.get_style().paint_layout(window,
                                        Gtk.StateType.NORMAL,
                                        True,
                                        cell_area,
                                        widget,
                                        'foo',
                                        cell_area.x + x_offset,
                                        cell_area.y + y_offset,
                                        pl)

    def do_set_property(self, gprop, value):
        setattr(self, gprop.name, value)

GObject.type_register(CellRendererDate)


class CellRendererDatetime(CellRendererDate):
    datetime = None
##     editable = None

    __gproperties__ = {
        'datetime': (GObject.TYPE_PYOBJECT,
                     'datetime of cell',
                     'datetime object contained in cell',
                     GObject.PARAM_READWRITE)
    }

    __gsignals__ = {
        'datetime-changed': (GObject.SignalFlags.RUN_FIRST, None,
                             (GObject.TYPE_STRING, GObject.TYPE_PYOBJECT)
                             )
    }

    def __init__(self, master, field_name, *args, **kwargs):
        self.datetime = None
        self.master = master
        self.field_name = field_name

        return Gtk.CellRenderer.__gobject_init__(self, *args, **kwargs)

    def do_pango_layout(self, widget):
        pc = widget.get_pango_context()
        pl = Pango.Layout(pc)
        pl.set_text(self.date_formatter(self.datetime))
        return pl

    def do_start_editing(self, event, widget, path, background_area,
                         cell_area, flags):

        if self.datetime is None:
            date_time = datetime.now()
        else:
            date_time = self.datetime
        #dbg.ddir(cell_area)
        ce = CellEditableCalendar(datetime=date_time, cell_area=cell_area,
                                  wdg=widget,
                                  fmt_func=self.master.gui_fields[self.field_name].format_value)

#        ce = CellEditableCalendar(date = date, pos=(event.x, event.y))

        ce.show()
        ce.grab_focus()
        ce.connect('editing-done', self.editing_done, widget, path)

        return ce

    def editing_done(self, widget, treeview, path):

        self.stop_editing(True)
        self.emit('datetime-changed', path, widget.datetime)
        return True


MAX_CHARS = 30

class CellRendererVarchar(Gtk.CellRendererText):

    """
    A text renderer whose width is decided in advance, not by the content.

    The width is either ``lenght`` average characters (capped at MAX_CHARS)
    or, if ``samples`` is given, the width of the widest sample text, e.g. a
    few dates formatted with the format of the column: exact for any format
    and locale.

    :param lenght: width in characters
    :param samples: a callable returning the list of sample strings
    :param samples_key: a callable returning a hashable value that changes
           when the samples change (e.g. the format of the field): samples
           are measured again only when it changes

    Setting ``fixed_width`` to False falls back to the content width
    (used by :func:`sqlkit.widgets.table.utils.zoom_to_fit`).

    GTK3 note: the width is enforced in ``do_get_preferred_width``; the GTK2
    ``do_get_size`` is never called by GTK3 size negotiation. A GtkTreeView
    sizes columns on the *minimum* width of their cells, which for an
    ellipsized text is just a few characters: the minimum is what we raise.
    """

    def __init__(self, lenght, samples=None, samples_key=None):
        GObject.GObject.__init__(self)
        self.lenght = lenght
        self.samples = samples
        self.samples_key = samples_key
        self.fixed_width = True
        self._width_cache = {}
        dbg.write("new varchar, lenght", lenght)

    def do_get_preferred_width(self, widget):
        minimum, natural = Gtk.CellRendererText.do_get_preferred_width(self, widget)
        if not self.fixed_width:
            return minimum, natural
        width = self.get_fixed_width(widget) + self.get_property('xpad') * 2
        return max(minimum, width), max(natural, width)

    def get_fixed_width(self, widget):
        """
        The width in pixels of the text area, cached per font and samples_key
        """
        context = widget.get_pango_context()
        description = context.get_font_description()
        key = (description.to_string() if description else None,
               self.samples_key() if self.samples_key else None)
        if key not in self._width_cache:
            self._width_cache[key] = self._measure(widget, context, description)
        return self._width_cache[key]

    def _measure(self, widget, context, description):
        samples = self.samples() if self.samples else None
        if samples:
            layout = widget.create_pango_layout('')
            widths = []
            for text in samples:
                layout.set_text(text, -1)
                widths.append(layout.get_pixel_size()[0])
            return max(widths)

        metrics = context.get_metrics(description)
        effective_lenght = min(self.lenght, MAX_CHARS) or MAX_CHARS
        # Pango uses its own unit (1/Pango.SCALE px); the C macro PANGO_PIXELS
        # is not available via introspection: round up to whole pixels
        pango_width = metrics.get_approximate_char_width() * effective_lenght
        return -(-pango_width // Pango.SCALE)


GObject.type_register(CellRendererVarchar)
