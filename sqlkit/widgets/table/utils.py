from sqlkit import debug as dbg
import gobject
import gtk

def set_height_request(treeview, rows=None):
    """Show "rows" rows in the treeview,
    or a reasonable number if "rows" is not set.
    Untested with multiline rows.
    """

    if not rows:
        rows = len(treeview.get_model())
        if rows == 0:
            rows = 10
        if rows > 30:
            rows = 30


    column      = treeview.get_column(0)
    cell_height = column.cell_get_size()[4]

    spacing = treeview.style_get_property('vertical-separator')

    needed_height = cell_height * rows + (spacing) * (rows-1)
    dbg.write('needed', needed_height, 'spacing', spacing)

    # This would not be needed if a previous call to "height-request" hadn't
    # been made. However, there was maybe a reason to do it.
    treeview.set_property('height-request', -1)

    toplevel        = treeview.get_toplevel()
    visible_rect    = treeview.get_visible_rect()
    missing_height  = needed_height - visible_rect.height
    new_width       = toplevel.get_allocation().width
    new_height      = toplevel.get_allocation().height + missing_height
#   print "toplevel:", toplevel, "old:", toplevel.get_allocation().height, "new:", new_height
    toplevel.resize(new_width, new_height)

def set_all_nonfilling(wid, level):
    """Set all widgets under the same toplevel as "wid" as non filling and non
    expanding (where this packing property has sense)."""
    if not level or not wid:
        return
    try:
        if wid.seen:
            return
    except:
        pass
#    print "browsed to", wid
    next_level = []
    try:
        parent = wid.get_parent()
        if hasattr(parent, 'child_set_property'):
            try:
                parent.child_set_property(wid, 'expand', False)
                parent.child_set_property(wid, 'fill', False)
            except:
                pass
            try:
                import gtk
                parent.child_set_property(wid, 'y-options', None)
            except:
                pass
        next_level.append(wid.get_parent())
    except:
        pass
    try:
        for child in wid.get_children():
            next_level.append(child)
    except:
        pass
    wid.seen = True
     

    for other in next_level:
        set_all_nonfilling(other, level-1)

def set_this_filling(wid):
    """Set all widgets over (parents, or grandparents... of) wid as filling and
    expanding (where those packing properties make sense)."""
    while wid:
        newwid = wid.get_parent()
        if gobject.type_is_a(wid, gtk.Alignment):
            wid.set_property('yscale',1)
            dbg.write("setting yscale:", wid)
        if gobject.type_is_a(newwid, gtk.Table):
            newwid.child_set_property(wid, 'y-options', gtk.FILL|gtk.EXPAND)
            dbg.write("setting y-options:", wid)
        wid = newwid

def set_this_filling_m2m(wid):
    wid.seen=True
    scrwin=wid.get_parent()
    scrwin.seen=True
    first_table=scrwin.get_parent()
    first_table.seen=True
    print "setting y-options of", scrwin
    first_table.child_set_property(scrwin, 'y-options',5)
    first_align = first_table.get_parent()
    first_align.seen=True
    print "setting yscale of", first_align
    first_align.set_property('yscale',1)
    second_table = first_align.get_parent()
    second_table.seen=True
    print "setting y-options of", first_align
    second_table.child_set_property(first_align, 'y-options',5)
    second_align = second_table.get_parent()
    second_align.seen=True
    print "setting yscale of", second_align
    second_align.set_property('yscale',1)
    third_table = second_align.get_parent()
    third_table.seen=True
    print "setting y-options of", first_align
    third_table.child_set_property(second_align, 'y-options',5)



def print_debug(wid):
    """Print debug information about packing of a widget and its superiors.
    """
    dbg.write("starting with", wid)
    number = 1 
    while wid:
        newwid = wid.get_parent()
        number += 1
        dbg.write("number", number, ":", newwid)
        try:
            dbg.write(newwid.get_property('xscale'), newwid.get_property('yscale'), "alignment")
            print "changing"
        except:
            pass
        try:
            dbg.write(newwid.get_allocation().width, newwid.get_allocation().height)
        except:
            pass
        try:
            dbg.write(newwid.get_property('n-rows'), newwid.get_property('n-columns'))
            dbg.write(newwid.child_get_property(wid, 'left-attach'), newwid.child_get_property(wid, 'top-attach'), newwid.child_get_property(wid, 'right-attach'), newwid.child_get_property(wid, 'bottom-attach'))
            dbg.write(newwid.get_children())
        except:
            pass
        wid = newwid

