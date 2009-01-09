from sqlkit import debug as dbg
import gobject
import gtk
import pango
from cell_renderers import CellRendererVarchar

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
    

def set_optimal_width(treeview, max_pixels=None):
    """
    Set optimal width of the treeview, based on width request by cellrenderers.

    This means that the window containing the treeview is resized accordingly
    (with care taken not to exit screen limit, and anyway not making the
    treeview larger that max_pixels, if set).
    If called before the treeview is realized (and with "resize" set), this
    function assumes that there is nothing else on the right and on the left of
    the treeview (e.g. the the treeview is in a bare sqltable).
    If called after, it supposes that, if there is something on the left and on
    the right, the treeview and all its parents have horizontal expand property
    set.
    """    

    widths = []


    columns = treeview.get_columns()
    titles = [column.get_title() for column in columns]
    model = treeview.get_model()
    rows_number = len(model)
    
    
    
    width_known = True
    
    for column_index in range(len(titles)):
        column = columns[column_index]
        cell_renderers = column.get_cell_renderers()
        renderers_widths = []
        # We have 3 possibilities:
        # 1) the renderer has a fixed width (the member "fixed_width" is set in
        #    table.py): we just take this as its width
        # 2) the renderer has a variable size and its criterion for populating
        #    is set in table.py: then, it also has a member 'cells_data_func',
        #    which contain informations about the criterion, and we use it to
        #    populate and ask get_size()
        # 3) the renderer wasn't set in table.py: we just take a constant size.
        
        for renderer in cell_renderers:
            if hasattr(renderer, 'fixed_width') and renderer.fixed_width:
                renderers_widths.append(renderer.get_size(treeview, None)[2])
            elif hasattr(column, 'cells_data_func'):
            # We'll have to check with all values that populate the column.
                renderer_func = None
                for cell_func in column.cells_data_func:
                    if cell_func[0] == renderer:
                        renderer_func = cell_func[1]
                        renderer_func_data = cell_func[2:]
                        break
                if renderer_func:
                    # This will be the minimum (for non populated columns).
                    max_width = 30
                    for row_index in range(rows_number):
                        iter = model.get_iter(row_index)
                        renderer_func(column, renderer, model, iter, *renderer_func_data)
                        if gobject.type_is_a(renderer, gtk.CellRendererText):
                            ellipsize = renderer.get_property('ellipsize')
                            renderer.set_property('ellipsize', False)
                        width = renderer.get_size(treeview, None)[2]
                        if gobject.type_is_a(renderer, gtk.CellRendererText):
                            # Put things back in order.
                            renderer.set_property('ellipsize', ellipsize)
                        max_width = max(max_width, width)
                    renderers_widths.append(max_width)
                else:
                    # The renderer was not found!
                    width_known = False
                    break
            else:
                # Don't know how to populate the renderer!                   
                width_known = False
                break
                
        top_widget = column.get_property('widget')
        top_width = top_widget.get_allocation().width

        expected_width = sum(renderers_widths)
        expected_width += len(cell_renderers)*treeview.style_get_property('horizontal-separator')
        widths.append(max(expected_width, top_width) + 4)   # FIXME: clarify this 4

    if width_known:
        total_desired_width = sum(widths)
    else:
        total_desired_width = treeview.get_size_request()[0]

    
    toplevel = treeview.get_toplevel()

    current_width = treeview.get_visible_rect().width

    if toplevel.window:
        # This means the window has already been realized and we can know
        # exactly which width of it is not occupied by columns:
        total_allocation = toplevel.window.get_frame_extents()
        total_width = total_allocation.width
        extra_space = total_width - current_width
        dbg.write("extra space", extra_space)
        total_desired_width += extra_space
    else:
        # The window is not realized. We assume there is _only_ the treeview,
        # plus the border
        total_desired_width += 10   # FIXME: tune this border

    available_width = get_effective_screen_width()

    if max_pixels:
        # If set, clip to max_pixels
        available_width = min(max_pixels, available_width)

    current_height = toplevel.get_size()[1]
    toplevel.resize(min(total_desired_width, available_width), current_height)
    treeview.columns_autosize()


def zoom_to_fit(treeview, resize=True):
    """Take a treeview (presumably from a sqlmask) and, for each column rendered
    by a CellRendererVarchar, reset space request criterion to content only (not
    database lenght introspection).
    Then, if "resize" is True, resize window accordingly.
    """
    columns = treeview.get_columns()
    for column in columns:
        renderers = column.get_cell_renderers()
        for renderer in renderers:
            if gobject.type_is_a(renderer, CellRendererVarchar):
                # Let's fall back to the usual CellRendererText...
                renderer.fixed_width = False
        column.set_expand(True)
        column.set_min_width(0)

    if resize:
        set_optimal_width(treeview)

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

