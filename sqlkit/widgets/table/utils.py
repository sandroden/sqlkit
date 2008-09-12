def set_height_request(treeview, rows):
    """Show a given number of rows in the treeview.
    Untested with multiline rows.
    """

    column      = treeview.get_column(0)
    cell_height = column.cell_get_size()[4]

    spacing = self.treeview.style_get_property('vertical-separator')

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
    toplevel.resize(new_width, new_height)
        

