"""Bricks/frames

An example of a frame

"""


lay = """
   uno 
   {|T.table
      abra cadabra
      dumba balu
      } -
"""

from gi.repository import Gtk

l = Layout(lay, opts="-")

w = l.show()
#w['F.table'].set_label('frame label')
