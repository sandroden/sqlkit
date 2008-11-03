"""bricks/toolbutt calendar

"""



lay = """
   {O tb=cal tb=gtk-new }
   l=esempio_calendario
"""

factory = gtk.IconFactory()
pixbuf = gtk.gdk.pixbuf_new_from_file('cal.gif')
iconset = gtk.IconSet(pixbuf)
factory.add('cal', iconset)
factory.add_default()


l=Layout(lay)

w = l.show()

tb = w['tb=cal']
tb.set_stock_id('cal')
#lbl = tb.get_children()[0].get_children()[0].get_children()[1]
#lbl.set_label('Calendar')
