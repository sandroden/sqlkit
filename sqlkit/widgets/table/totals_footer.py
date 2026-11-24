# Copyright (C) 2026, Sandro Dentella <sandro@e-den.it>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Totals footer
=============

A one-row, always visible strip placed right under the table that shows the
grand totals computed by :class:`sqlkit.widgets.table.totals.Totals`, each
one under its own column. It mirrors the columns of the main treeview:

* width     -> bound to the width of the corresponding main column
* visibility-> bound to the visibility of the corresponding main column
* order     -> rebuilt on ``columns-changed`` of the main treeview
* horizontal scroll -> follows the horizontal adjustment of the table

The grand total row inside the table is left untouched: the footer is an
extra view of the same values, useful when the table has many rows. While
that row is entirely visible the footer is made transparent (its space is
kept, so the table does not change height while scrolling).
"""

from gi.repository import Gtk, GObject, GLib

from sqlkit import debug as dbg


class TotalsFooter(object):

    """
    A fixed strip with the grand totals, shown under the treeview of a table.

    Created lazily by :class:`Totals` the first time a total is shown.
    """

    def __init__(self, totals):
        self.totals = totals
        self.table = totals.table
        self.main_tv = totals.treeview
        self.main_sw = self.main_tv.get_parent()
        self._bindings = []
        self._handlers = []

        self.store = Gtk.ListStore(object)
        self.total_obj = totals.total_class(self.table.field_list, sub=False)
        self.store.append([self.total_obj])

        self.tv = Gtk.TreeView(model=self.store)
        self.tv.set_headers_visible(False)
        self.tv.set_can_focus(False)
        self.tv.get_selection().set_mode(Gtk.SelectionMode.NONE)

        self.sw = Gtk.ScrolledWindow()
        # EXTERNAL: no scrollbar, but the content can be scrolled by us
        self.sw.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)
        self.sw.set_shadow_type(self.main_sw.get_shadow_type())
        self.sw.add(self.tv)

        self.main_tv.connect('columns-changed', lambda tv: self.rebuild())
        main_hadj = self.main_sw.get_hadjustment()
        main_hadj.connect('value-changed', self._sync_scroll)
        self.sw.get_hadjustment().connect('changed', self._sync_scroll)

        # the footer is transparent while the grand total row is visible
        self._check_id = None
        main_vadj = self.main_sw.get_vadjustment()
        main_vadj.connect('value-changed', self._queue_check)
        main_vadj.connect('changed', self._queue_check)
        self.main_tv.connect('size-allocate', self._queue_check)

        self.rebuild()
        self.attached = self._attach()

    @classmethod
    def can_attach(cls, treeview):
        """
        True if the treeview lives in a ScrolledWindow whose container
        we know how to extend (Gtk.Grid or Gtk.Box)
        """
        sw = treeview.get_parent()
        if not isinstance(sw, Gtk.ScrolledWindow):
            return False
        return isinstance(sw.get_parent(), (Gtk.Grid, Gtk.Box))

    def _attach(self):
        """
        Place the footer right under the ScrolledWindow of the table
        """
        container = self.main_sw.get_parent()
        if isinstance(container, Gtk.Grid):
            left, top, width, height = container.child_get(
                self.main_sw, 'left-attach', 'top-attach', 'width', 'height')
            container.insert_next_to(self.main_sw, Gtk.PositionType.BOTTOM)
            container.attach(self.sw, left, top + height, width, 1)
        elif isinstance(container, Gtk.Box):
            container.pack_start(self.sw, False, True, 0)
            position = container.child_get_property(self.main_sw, 'position')
            container.reorder_child(self.sw, position + 1)
        else:
            dbg.write("TotalsFooter: unsupported container %s" % container)
            return False
        self.sw.set_hexpand(True)
        self.sw.set_vexpand(False)
        return True

    def _sync_scroll(self, *args):
        value = self.main_sw.get_hadjustment().get_value()
        self.sw.get_hadjustment().set_value(value)

    def _disconnect(self):
        for binding in self._bindings:
            binding.unbind()
        self._bindings = []
        for column in self.tv.get_columns():
            self.tv.remove_column(column)

    def rebuild(self):
        """
        (Re)create the footer columns mirroring the main treeview columns
        """
        self._disconnect()
        for main_col in self.main_tv.get_columns():
            self.tv.append_column(self._make_column(main_col))
        self.tv.queue_draw()

    def _make_column(self, main_col):
        field_name = getattr(main_col, 'field_name', None)
        column = Gtk.TreeViewColumn()
        column.field_name = field_name
        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        cell = Gtk.CellRendererText()
        main_cells = main_col.get_cells()
        if main_cells:
            cell.set_property('xalign', main_cells[0].get_property('xalign'))
        column.pack_start(cell, True)
        column.set_cell_data_func(cell, self._cell_data_func, field_name)

        flags = GObject.BindingFlags.SYNC_CREATE
        self._bindings += [
            main_col.bind_property('width', column, 'fixed-width', flags),
            main_col.bind_property('visible', column, 'visible', flags),
        ]
        return column

    def _cell_data_func(self, column, cell, model, iter, field_name):
        obj = model.get_value(iter, 0)
        cell.set_property('cell-background', obj._color)
        if field_name in self.totals.totals:
            field = self.table.gui_fields[field_name]
            value = self.totals.totals[field_name]
            text = GLib.markup_escape_text(str(field.format_value(value)))
            obj.set_value_and_colors(cell, text, field_name)
        else:
            cell.set_property('markup', '')

    def refresh(self):
        """
        Show the current grand totals, or hide the footer if no total is shown
        """
        visible = bool(self.totals.totals) and not self.totals.hide_total
        self.sw.set_visible(visible)
        if visible:
            self.sw.show_all()
            self.tv.queue_draw()
            self._queue_check()
        self.fit_widths(visible)

    def _queue_check(self, *args):
        """
        Schedule a check of the grand total row visibility. Done in idle:
        row positions are only known after the treeview has been laid out
        """
        if self._check_id is None:
            self._check_id = GLib.idle_add(self._check_total_row)

    def _check_total_row(self):
        self._check_id = None
        # opacity rather than hide: the space stays reserved so the table
        # does not change height (and jump) while scrolling to the bottom
        self.sw.set_opacity(0.0 if self.total_row_visible() else 1.0)
        return False

    def total_row_visible(self):
        """
        True if the grand total row of the table is entirely visible, in
        which case the footer would just repeat it
        """
        model = self.main_tv.get_model()
        if model is None or not self.main_tv.get_realized():
            return False
        n_rows = model.iter_n_children(None)
        if not n_rows:
            return False
        path = Gtk.TreePath(n_rows - 1)
        obj = model[path][0]
        if not isinstance(obj, self.totals.total_class) or obj._sub:
            return False
        rect = self.main_tv.get_cell_area(path, None)
        visible_height = self.main_tv.get_visible_rect().height
        return rect.height > 0 and rect.y >= 0 and rect.y + rect.height <= visible_height

    def fit_widths(self, visible=True):
        """
        Make each main column with a total at least as wide as its total.

        Columns are sized on the record values, a total is normally wider and
        would be clipped (both here and in the grand total row of the table).
        The min-width of the main column is only raised, never lowered below
        the value it had before the footer touched it, and it is restored when
        the total is removed or the footer hidden.
        """
        separator = self.tv.style_get_property('horizontal-separator')
        iter = self.store.get_iter_first()
        for main_col, column in zip(self.main_tv.get_columns(), self.tv.get_columns()):
            orig = getattr(main_col, '_footer_orig_min_width', None)
            if not visible or column.field_name not in self.totals.totals:
                if orig is not None:
                    main_col.set_min_width(orig)
                    del main_col._footer_orig_min_width
                continue
            column.cell_set_cell_data(self.store, iter, False, False)
            cell = column.get_cells()[0]
            needed = cell.get_preferred_width(self.tv).natural_size + separator
            if orig is None:
                orig = main_col._footer_orig_min_width = main_col.get_min_width()
            main_col.set_min_width(max(orig, needed))
