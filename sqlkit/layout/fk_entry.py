"""
An entry with an arrow. Similar to comboBoxEdit but with possibility to
connect to click on the arrow

"""
from gi.repository import GObject
from gi.repository import Gtk

from sqlkit import _


class FkEdit(Gtk.Entry):
    __gtype_name__ = 'FkEntry'

    __gsignals__ = {
        'completion-requested': (GObject.SignalFlags.RUN_LAST, None,
                                 (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.props.secondary_icon_stock = 'gtk-find'
        self.props.secondary_icon_tooltip_text = _(
            "Find allowed values (Control-Enter/Shift-Enter)")
        #self.props.secondary_icon_stock = None
        self.connect('icon-press', self.icon_press_cb)

    def icon_press_cb(self, entry, icon_pos, event):
        self.emit('completion-requested', event)
