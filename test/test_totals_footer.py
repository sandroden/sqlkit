"""TotalsFooter: the fixed strip with grand totals under a SqlTable.

GTK widgets are built for real, so the module carries the ``gtk`` marker and
must run under ``xvfb-run -a``.
"""
import os
from decimal import Decimal

import pytest

pytestmark = pytest.mark.gtk


@pytest.fixture
def footer_db():
    for var in ("LC_ALL", "LC_NUMERIC", "LC_TIME", "LANG"):
        os.environ[var] = "en_US.UTF-8"

    from sqlalchemy import Column, Integer, Numeric, String, create_engine
    from sqlalchemy.orm import declarative_base

    from sqlkit.db import proxy
    from conftest import drop_schema

    Base = declarative_base()

    class Hours(Base):
        __tablename__ = "sk_totals_footer"
        id = Column(Integer, primary_key=True)
        name = Column(String(60))
        qty = Column(Numeric(8, 2))

    url = os.environ.get("SQLKIT_TEST_DB_URL") or "sqlite://"
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(Hours.__table__.insert(), [
            {"name": "row%02d" % i, "qty": Decimal("1.25")} for i in range(40)
        ])
    db = proxy.DbProxy(engine=engine, metadata=Base.metadata)
    yield Hours, db
    engine.dispose()
    drop_schema(Base.metadata)


def flush_events():
    from gi.repository import Gtk
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def footer_text(table, field_name):
    """Render the footer cell of field_name and return its markup"""
    footer = table.totals._footer
    for col in footer.tv.get_columns():
        if col.field_name == field_name:
            col.cell_set_cell_data(footer.store, footer.store.get_iter_first(), False, False)
            return col.get_cells()[0].get_property('text')
    raise KeyError(field_name)


def make_table(footer_db, **kw):
    from sqlkit.widgets import SqlTable
    Hours, db = footer_db
    t = SqlTable(Hours, dbproxy=db, show=False, **kw)
    t.reload()
    return t


def test_no_footer_without_totals(footer_db):
    t = make_table(footer_db)
    assert t.totals._footer is None


def test_footer_created_under_the_table(footer_db):
    from gi.repository import Gtk
    t = make_table(footer_db)
    t.totals.add_total('qty')
    footer = t.totals._footer
    assert footer is not None and footer.attached

    grid = t.widgets['S=tree'].get_parent()
    assert isinstance(grid, Gtk.Grid)
    assert footer.sw.get_parent() is grid
    sw_top, sw_height = grid.child_get(t.widgets['S=tree'], 'top-attach', 'height')
    assert grid.child_get_property(footer.sw, 'top-attach') == sw_top + sw_height
    assert footer.sw.get_visible()


def test_footer_shows_grand_total(footer_db):
    t = make_table(footer_db)
    t.totals.add_total('qty')
    assert t.totals.totals['qty'] == Decimal('50.00')
    assert '50' in footer_text(t, 'qty')
    assert footer_text(t, 'name') == ''


def test_footer_mirrors_columns(footer_db):
    t = make_table(footer_db)
    t.totals.add_total('qty')
    footer = t.totals._footer
    main_cols = t.treeview.get_columns()
    assert len(footer.tv.get_columns()) == len(main_cols)

    # visibility follows the main column
    main_cols[0].set_visible(False)
    assert not footer.tv.get_columns()[0].get_visible()
    main_cols[0].set_visible(True)
    assert footer.tv.get_columns()[0].get_visible()

    # reordering rebuilds the footer in the new order
    before = [c.field_name for c in t.treeview.get_columns()]
    t.treeview.move_column_after(main_cols[0], main_cols[-1])
    names = [c.field_name for c in t.treeview.get_columns()]
    assert names != before
    assert [c.field_name for c in footer.tv.get_columns()] == names


def test_footer_widths_follow_main_columns(footer_db):
    t = make_table(footer_db)
    t.totals.add_total('qty')
    win = t.widgets['Window']
    win.resize(500, 300)
    win.show_all()
    flush_events()
    footer = t.totals._footer
    assert any(c.get_width() > 0 for c in t.treeview.get_columns())
    for main_col, fcol in zip(t.treeview.get_columns(), footer.tv.get_columns()):
        assert fcol.get_fixed_width() == main_col.get_width()


def test_columns_widened_to_fit_total(footer_db):
    """A total is wider than the row values: the column must not clip it"""
    t = make_table(footer_db)
    t.totals.add_total('qty')
    footer = t.totals._footer
    fcol = [c for c in footer.tv.get_columns() if c.field_name == 'qty'][0]
    fcol.cell_set_cell_data(footer.store, footer.store.get_iter_first(), False, False)
    needed = fcol.get_cells()[0].get_preferred_width(footer.tv).natural_size
    main_col = t.views['main'].tvcolumns['qty']
    assert main_col.get_min_width() >= needed > 0
    # columns without a total are left alone
    assert t.views['main'].tvcolumns['name'].get_min_width() == -1


def settle(seconds=0.5):
    """Run the main loop for a while: resize, idle callbacks, layout"""
    from gi.repository import GLib
    for _ in range(int(seconds * 20)):
        flush_events()
        GLib.usleep(50000)
    flush_events()


def shown_table(footer_db, height, **filters):
    t = make_table(footer_db)
    if filters:
        t.add_filter(**filters)
        t.reload()
    t.totals.add_total('qty')
    win = t.widgets['Window']
    win.resize(500, height)
    win.show_all()
    settle()
    return t


def test_footer_transparent_when_total_row_visible(footer_db):
    """Few rows (e.g. an inline of a record): the total row is in sight"""
    t = shown_table(footer_db, 600, name='row01')
    footer = t.totals._footer
    assert footer.total_row_visible()
    assert footer.sw.get_visible()           # space kept, no layout jump
    assert footer.sw.get_opacity() == 0.0


def test_footer_opaque_until_scrolled_to_total_row(footer_db):
    t = shown_table(footer_db, 300)
    footer = t.totals._footer
    assert not footer.total_row_visible()
    assert footer.sw.get_opacity() == 1.0

    vadj = t.widgets['S=tree'].get_vadjustment()
    vadj.set_value(vadj.get_upper() - vadj.get_page_size())
    settle()
    assert footer.total_row_visible()
    assert footer.sw.get_opacity() == 0.0

    vadj.set_value(0)
    settle()
    assert footer.sw.get_opacity() == 1.0


def test_footer_follows_records(footer_db):
    t = make_table(footer_db)
    t.totals.add_total('qty')
    t.reload()
    assert '50' in footer_text(t, 'qty')
    t.add_filter(name='nothing-matches')
    t.reload()
    assert t.totals.totals['qty'] == 0
    assert footer_text(t, 'qty').startswith('0')


def test_footer_disabled(footer_db):
    t = make_table(footer_db)
    t.totals.footer = False
    t.totals.add_total('qty')
    assert t.totals._footer is None


def test_footer_hidden_with_hide_total(footer_db):
    t = make_table(footer_db)
    t.totals.add_total('qty', hide_total=True)
    assert not t.totals._footer.sw.get_visible()


def test_footer_hidden_after_del_total(footer_db):
    t = make_table(footer_db)
    main_col = t.views['main'].tvcolumns['qty']
    orig_min_width = main_col.get_min_width()
    t.totals.add_total('qty')
    assert main_col.get_min_width() > orig_min_width
    t.totals.del_total('qty')
    assert not t.totals._footer.sw.get_visible()
    # the column is given back its original min-width
    assert main_col.get_min_width() == orig_min_width
