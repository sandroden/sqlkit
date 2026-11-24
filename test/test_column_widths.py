"""Initial width of SqlTable columns (CellRendererVarchar under GTK3).

GTK3 never calls the GTK2 ``do_get_size``: the width computed there (N chars
from db length / col_width / per-type minimum) was ignored and every
non-expanding column ended up as wide as its header, with dates shown as
``14/1…``. Widths are now enforced in ``do_get_preferred_width``; dates,
datetimes and numbers are measured on formatted samples.

Real GTK windows: run under
``env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a``.
"""
import os
from datetime import date, datetime
from decimal import Decimal

import pytest

pytestmark = pytest.mark.gtk


@pytest.fixture
def widths_db():
    for var in ("LC_ALL", "LC_NUMERIC", "LC_TIME", "LANG"):
        os.environ[var] = "en_US.UTF-8"

    from sqlalchemy import (Column, Date, DateTime, Integer, Numeric, String,
                            create_engine)
    from sqlalchemy.orm import declarative_base

    from sqlkit.db import proxy
    from conftest import drop_schema

    Base = declarative_base()

    class Work(Base):
        __tablename__ = "sk_column_widths"
        id = Column(Integer, primary_key=True)
        day = Column(Date)
        stamp = Column(DateTime)
        qty = Column(Numeric(8, 2))
        code = Column(String(12))
        descr = Column(String(200))

    url = os.environ.get("SQLKIT_TEST_DB_URL") or "sqlite://"
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(Work.__table__.insert(), [
            {"day": date(2026, 12, 28), "stamp": datetime(2026, 12, 28, 23, 58, 58),
             "qty": Decimal("12345.67"), "code": "ABCDEFGHIJKL",
             "descr": "a long description " * 10},
        ])
    db = proxy.DbProxy(engine=engine, metadata=Base.metadata)
    yield Work, db
    engine.dispose()
    drop_schema(Base.metadata)


def settle(seconds=0.5):
    from gi.repository import Gtk, GLib
    for _ in range(int(seconds * 20)):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        GLib.usleep(50000)


def text_width(widget, text):
    return widget.create_pango_layout(text).get_pixel_size()[0]


def shown_table(widths_db, setup=None, **kw):
    from sqlkit.widgets import SqlTable
    Work, db = widths_db
    t = SqlTable(Work, dbproxy=db, show=False,
                 field_list='day stamp qty code descr', **kw)
    if setup:
        setup(t)
    t.reload()
    win = t.widgets['Window']
    win.resize(700, 300)
    win.show_all()
    settle()
    return t


def assert_fits(t, field_name, text):
    """The text is not ellipsized: the column is at least as wide"""
    col = t.views['main'].tvcolumns[field_name]
    cell = col.get_cells()[0]
    room = col.get_width() - 2 * cell.get_property('xpad')
    needed = text_width(t.treeview, text)
    assert room >= needed, "%s: %d px for %r that needs %d px" % (
        field_name, room, text, needed)


def test_date_column_fits_its_dates(widths_db):
    t = shown_table(widths_db)
    day = t.gui_fields['day'].format_value(date(2026, 12, 28))
    assert_fits(t, 'day', day)


def test_datetime_column_fits(widths_db):
    t = shown_table(widths_db)
    stamp = t.gui_fields['stamp'].format_value(datetime(2026, 12, 28, 23, 58, 58))
    assert_fits(t, 'stamp', stamp)


def test_date_column_follows_format_set_after_creation(widths_db):
    """pysia sets gui_fields.<date>.format after creating the widget"""
    fmt = 'EEEE dd MMMM yyyy'

    def setup(t):
        t.gui_fields['day'].format = fmt

    t = shown_table(widths_db, setup=setup)
    # the widest weekday/month combination of the samples must fit
    widest = max((t.gui_fields['day'].format_value(d)
                  for d in t.views['main'].columns['day'].sample_values()),
                 key=lambda s: text_width(t.treeview, s))
    assert_fits(t, 'day', widest)


def test_numeric_column_fits_digits(widths_db):
    t = shown_table(widths_db)
    assert_fits(t, 'qty', t.gui_fields['qty'].format_value(Decimal('12345.67')))


def test_short_varchar_sized_on_db_length(widths_db):
    """String(12): about 12 average chars, not just the header width"""
    t = shown_table(widths_db)
    col = t.views['main'].tvcolumns['code']
    header = text_width(t.treeview, 'code')
    assert col.get_width() > 2 * header
    assert_fits(t, 'code', 'ABCDEFGH')


def test_col_width_is_honoured(widths_db):
    """col_width (in average chars, capped at MAX_CHARS) beats the db length"""
    default = shown_table(widths_db).views['main'].tvcolumns['code'].get_width()
    t = shown_table(widths_db, col_width={'code': 25})
    col = t.views['main'].tvcolumns['code']
    assert col.get_width() > 1.8 * default


def test_fixed_width_off_falls_back_to_content(widths_db):
    """zoom_to_fit switches fixed_width off: the renderer sizes on content"""
    t = shown_table(widths_db)
    cell = t.views['main'].tvcolumns['code'].get_cells()[0]
    fixed_min = cell.get_preferred_width(t.treeview).minimum_size
    cell.fixed_width = False
    content_min = cell.get_preferred_width(t.treeview).minimum_size
    assert content_min < fixed_min
