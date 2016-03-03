"""
An entry with an arrow. Similar to comboBoxEdit but with possibility to
connect to click on the arrow

"""
from gi.repository import GObject
from gi.repository import Gtk

from sqlkit import _

if Gtk.gtk_version >= (2, 16):

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

else:

    class FkEdit(Gtk.HBox):
        __gtype_name__ = 'FkEntry'

        __gsignals__ = {
            'completion-requested': (GObject.SignalFlags.RUN_LAST, None,
                                     (GObject.TYPE_PYOBJECT,)),
        }

        def __init__(self):
            GObject.GObject.__init__(self)
            self.entry = Gtk.Entry()

            # the date button
            self.button = Gtk.Button()

            self._align_entry = Gtk.Alignment.new(1, 0, 1, 0)
            self._align_arrow = Gtk.Alignment.new(0, 0, 0, 0)

            self._align_entry.add(self.entry)
            self._align_arrow.add(self.button)

            self.add(self._align_entry)
            self.add(self._align_arrow)
            # the down arrow
            arrow = Gtk.Arrow(Gtk.ArrowType.DOWN, Gtk.ShadowType.OUT)
            self.button.add(arrow)
            arrow.show()
            # finally show the button
            self._align_entry.show_all()
            self._align_arrow.show_all()

            self.button.connect('button-press-event', self.button_press_cb)

            self.connect('realize', self.set_packing)

        def button_press_cb(self, button, event):
            self.emit('completion-requested', event)

        def modify_base(self, state, color):
            self.entry.modify_base(state, color)

        def set_packing(self, other):
            parent = self.get_parent()
            props = [prop.name for prop in parent.list_child_properties()]
            if 'y-options' in props:
                parent.child_set_property(self, 'y-options', 0)
