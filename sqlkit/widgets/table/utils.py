from sqlkit import debug as dbg
import gobject
import gtk
import pango

def set_height_request(treeview, rows=None):
    """
    Show "rows" rows in the treeview,
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
    
def get_string_exact_width(context, string):
    """
    (render and) Return width of a string in given context.
    """
    description = context.get_font_description()
    layout = pango.Layout(context)
    layout.set_text(string)
    width = layout.get_pixel_extents()[1][2]
    return width

def get_string_width(context, string=None, chars_num=80):
    """
    Find how much space is needed to render a string of "chars_num"
    characters in pango context "context". If "string" is given, compute this
    number exactly, actually recomputing rendering of the string.
    Otherwise, use the "approximate_chars_width" of the font.
    """
    if string != None:
        dbg.write("calculating width of", string[:chars_num], chars_num, type(string))
        return get_string_exact_width(context, string[:chars_num])
    else:
        # Perfection would imply setting this to actual language
        language = None
        description = context.get_font_description()
        metrics = context.get_metrics(description)
        # Pango uses its own internal measure unit. "pango.PIXELS" converts it.
        pango_width = metrics.get_approximate_char_width()*chars_num
        width = pango.PIXELS(pango_width)
        return width
        
def get_effective_screen_width():
    """
    Ugly hack. Couldn't find anything better. And in fact it's not strange,
    since GNOME HIGs apparently don't like this.
    """
    root = gtk.gdk.get_default_root_window()
    prop = gtk.gdk.atom_intern('_NET_WORKAREA')
    fields = root.property_get(prop)
    sizes = fields[2]
    width = sizes[2]
    return width

def free_column(column):
    """
    Free a column from restriction on its resizeability.
    """
    print "freeing", column
    column.set_min_width(0)
    column.set_max_width(2000)
    

def set_optimal_width(treeview, sqltable=None, resize=True, max_pixels=None):
    """
    Set optimal width of the columns and of the whole treeview, meaning that:
    - if the treeview is already populated, by looking at shown data we
      calculate optimal size to fit the data
    - if the treeview is not populated but sqltable is given, by introspection
      we get a reasonable size.
    If "resize" is True, the window is resized accordingly (with care taken not
    to exit screen limit, and anyway not making the treeview larger that
    max_pixels, if set), otherwise only a redestribution of horizontal space
    among columns is done.
    If called before the treeview is realized (and with "resize" set), this
    function assumes that there is nothing else on the right and on the left of
    the treeview (e.g. the the treeview is in a bare sqltable).
    If called after, it supposes that, if there is something on the left and on
    the right, the treeview and all its parents have horizontal expand property
    set.
    Notice "resize=False" doesn't make sense if the treeview is still not
    realized, since it still has no dimension to stick to.
    """    

    widths = []


    columns = treeview.get_columns()
    titles = [column.get_title() for column in columns]

    model = treeview.get_model()
    rows_number = len(model)

    if rows_number:
        # There already is some data shown
        for column_index in range(len(titles)):
            for row_index in range(rows_number):
                item = model.get_value(model.get_iter(row_index), column_index)
                string = item.__dict__[attribute_name]
                string_width = get_string_width(treeview.get_pango_context(), string, chars_num=100)
                dbg.write(string[:chars_num], string_width)
                max_string_width = max(max_string_width, string_width)
            widths.append(max_string_width)
    elif sqltable:
        # No data shown, but we can get optimal widths by introspection
        for column_index in range(len(titles)):
            title = titles[column_index]
            vfield = title.replace(' ', '_')
            maxchars = sqltable.vfields[vfield].db_spec['length']
            if maxchars:
                context = treeview.get_pango_context()
                expected_width = get_string_width(context, chars_num=maxchars)
            else:
                # We have no information on data... just fix size (FIXME?)
                expected_width = 100
            widths.append(expected_width)
    else:
        # No data shown, no table informations... nothing to do!
        return
    
    total_desired_width = sum(widths)

    toplevel = treeview.get_toplevel()

    current_widths = [column.get_width() for column in columns]
    columns_current_width = sum(current_widths)

    if resize:
        if toplevel.window:
            # This means the window has already been realized and we can know
            # exactly which width of it is not occupied by columns:
            total_allocation = toplevel.window.get_frame_extents()
            total_width = total_allocation.width
            extra_space = total_width - columns_current_width
            available_width = get_effective_screen_width() - extra_space
            if max_pixels:
                available_width = min(max_pixels, available_width)
        else:
            # The window is not realized. We assume there is _only_ the treeview
            available_width = get_effective_screen_width()
            print "available_width is", available_width
        if max_pixels:
            # If set, clip to max_pixels
            available_width = min(max_pixels, available_width)
    else:
        print "resize false"
        # The available width is just the one currently occupied
        available_width = columns_current_width
        
    print "available_width is", available_width
    available_percentage = float(available_width)/total_desired_width
    print "available_percentage is", available_percentage

    print "totale:", sum(widths)
        
    if resize:
        current_height = toplevel.get_size()[1]
        toplevel.resize(min(total_desired_width, available_width), current_height)
    
    if available_percentage < 1 or not resize:
        # Some clipping is needed, or vice-versa we have too much space and,
        # since we won't resize, we want to occupy it all
        for index in range(len(widths)):
            print widths[index]
            widths[index] = widths[index]*available_percentage
        print available_percentage            
    for index in range(len(titles)):
        column = columns[index]
        # Hack. No gtk method to explicitly resize a column exists.
        column.set_min_width(int(widths[index]))
        column.set_max_width(int(widths[index]))
        gobject.timeout_add_seconds(1, free_column, column)

def set_all_nonfilling(wid, level):
    """
    Set all widgets under the same toplevel as "wid" as non filling and non
    expanding (where this packing property has sense).
    """
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
    """
    Set all widgets over (parents, or grandparents... of) wid as filling and
    expanding (where those packing properties make sense).
    """
    while wid:
        newwid = wid.get_parent()
        if gobject.type_is_a(wid, gtk.Alignment):
            wid.set_property('yscale',1)
            dbg.write("setting yscale:", wid)
        if gobject.type_is_a(newwid, gtk.Table):
            newwid.child_set_property(wid, 'y-options', gtk.FILL|gtk.EXPAND)
            dbg.write("setting y-options:", wid)
        wid = newwid

def print_debug(wid):
    """
    Print debug information about packing of a widget and its superiors.
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

