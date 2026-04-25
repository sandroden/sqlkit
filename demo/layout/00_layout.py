"""Bricks/Gtk.Layout


"""
from gi.repository import Gtk

lay = """
   LS=a
"""

l = Layout(lay, opts="T")

w = l.show()
e = Gtk.Entry()

def drag_begin_cb(*args):
    print('BEGIN')

def drag_end_cb(*args):
    dbg.write('END')

def drag_motion_cb(*args):
    dbg.write('MOTION')


lay = w['Lay=a']
lay.connect("drag_begin", drag_begin_cb)
lay.connect("drag_end",   drag_end_cb)
lay.connect("drag_motion", drag_motion_cb)

w['Lay=a'].put(e, 50, 50)
# In GTK3 a Gtk.Layout inside a Gtk.ScrolledWindow does not honour
# width-request/height-request: the ScrolledWindow asks the child for
# its natural size and Gtk.Layout reports 0x0. Use Gtk.Layout.set_size()
# to declare the scrollable canvas, and min-content-* on the
# ScrolledWindow to control the viewport size.
w['Lay=a'].set_size(300, 300)
l.prop('S=a', 'min-content-width', 300)
l.prop('S=a', 'min-content-height', 300)
e.show()
