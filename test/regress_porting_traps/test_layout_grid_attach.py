"""Trap: layout flag 'T' must produce a Gtk.Grid (not a Gtk.Table) and
the 4-arg Gtk.Table.attach(left, right, top, bottom) idiom must be
translated to Gtk.Grid.attach(child, left, top, width, height) with the
implicit GTK_EXPAND|GTK_FILL replaced by hexpand=True/vexpand=True on
the child (Grid children default to no expand, which would collapse the
layout if not set).
"""
from _harness import ensure_path, run_tests
ensure_path()

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

from sqlkit.layout.layout import Layout  # noqa: E402
from sqlkit.layout.widgets import Table, _W  # noqa: E402


def test_table_class_targets_grid():
    assert Table.gtkClass == 'GtkGrid'


def test_T_flag_still_maps_to_table_class():
    # Layouts that say 'T' must keep working even though we swapped the
    # backing GTK widget under the hood.
    assert _W['T'] is Table


def _build(layout_string):
    lay = Layout(layout_string, opts='V')
    win = lay.show()
    return lay, win


def test_layout_T_creates_gtk_grid():
    lay, w = _build("""{T.demo l=hi e=who }""")
    container = w['T.demo']
    assert isinstance(container, Gtk.Grid), type(container)


def test_grid_packing_xml_emits_grid_props_only():
    # _packing_xml must filter through Gtk.Grid.list_child_properties and
    # therefore must NOT emit Table-only 'right_attach'/'bottom_attach'.
    lay, w = _build("""{T.demo e=who }""")
    entry = w['e=who']
    parent = entry.get_parent()
    assert isinstance(parent, Gtk.Grid)
    valid = {p.name for p in parent.list_child_properties()}
    assert 'left-attach' in valid
    assert 'top-attach' in valid
    assert 'width' in valid
    assert 'height' in valid
    assert 'right-attach' not in valid
    assert 'bottom-attach' not in valid


def test_layout_with_span_does_not_warn():
    # Two-column span via '- -' must not raise GtkWarnings about unknown
    # child properties on Gtk.Grid.
    lay, w = _build("""
        {T.demo a   b   c
                d   -   -
        }
    """)
    grid = w['T.demo']
    assert isinstance(grid, Gtk.Grid)


if __name__ == '__main__':
    run_tests(globals())
