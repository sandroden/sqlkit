"""Smoke tests for SqlMask / SqlTable on a sqlite in-memory db.

These build real GTK3 widgets, so they carry the ``gtk`` marker and must run
under ``xvfb-run -a``.

We use a *relationship-free* declarative model: InspectMapper (used internally
by the widgets) currently crashes on mappers that carry relationship
properties (see test_minspect.py::test_minspect_relationship_property_crashes),
which is a pre-existing library limitation, not what these smoke tests target.

We also avoid ``naked=True``: when the optional ``appy`` printing engine is
installed, the naked layout omits the status bar that PrintToolAppy expects,
raising ``KeyError: 'sb=StBar'`` (printing.py PrintToolAppy.__init__).  A
normal (non-naked) widget builds cleanly regardless of appy.
"""
import os

import pytest

pytestmark = pytest.mark.gtk


@pytest.fixture
def simple_dbproxy():
    """A relationship-free declarative model on a fresh sqlite engine.

    Pin locale to en_US so any field formatting is deterministic.
    """
    for var in ("LC_ALL", "LC_NUMERIC", "LC_TIME", "LANG"):
        os.environ[var] = "en_US.UTF-8"

    from sqlalchemy import Boolean, Column, Date, Integer, Numeric, String, create_engine
    from sqlalchemy.orm import declarative_base

    from sqlkit.db import proxy

    Base = declarative_base()

    class Simple(Base):
        # Prefix the table name so a shared backend (PG) does not collide with
        # other suites / leftovers across runs.
        __tablename__ = "sk_smoke_simple"
        id = Column(Integer, primary_key=True)
        name = Column(String(60))
        qty = Column(Integer)
        price = Column(Numeric(8, 2))
        born = Column(Date)
        active = Column(Boolean)

    # Default sqlite in-memory; bind to SQLKIT_TEST_DB_URL when set.
    url = os.environ.get("SQLKIT_TEST_DB_URL") or "sqlite://"
    from conftest import drop_schema

    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = proxy.DbProxy(engine=engine, metadata=Base.metadata)
    yield Simple, db
    # The widgets open DbProxy sessions that, on SA2 / PostgreSQL, leave a
    # connection "idle in transaction" holding a lock on the table; that would
    # block the teardown DROP forever.  Dispose the proxy's engine first, then
    # drop via the shared helper (which terminates leftover backends on PG).
    engine.dispose()
    drop_schema(Base.metadata)


def test_sqlmask_instantiates(simple_dbproxy):
    from sqlkit.widgets import SqlMask

    Simple, db = simple_dbproxy
    sm = SqlMask(Simple, dbproxy=db, show=False)
    assert sm is not None
    # the introspected gui fields are present
    assert "name" in sm.gui_fields
    assert "qty" in sm.gui_fields


def test_sqltable_instantiates(simple_dbproxy):
    from sqlkit.widgets import SqlTable

    Simple, db = simple_dbproxy
    st = SqlTable(Simple, dbproxy=db, show=False)
    assert st is not None
    assert "name" in st.gui_fields


def test_sqlmask_varchar_set_get_roundtrip(simple_dbproxy):
    from sqlkit.widgets import SqlMask

    Simple, db = simple_dbproxy
    sm = SqlMask(Simple, dbproxy=db, show=False)
    field = sm.gui_fields["name"]
    field.set_value("hello")
    assert field.get_value() == "hello"


def test_sqlmask_integer_set_get_roundtrip(simple_dbproxy):
    from sqlkit.widgets import SqlMask

    Simple, db = simple_dbproxy
    sm = SqlMask(Simple, dbproxy=db, show=False)
    field = sm.gui_fields["qty"]
    field.set_value(42)
    assert field.get_value() == 42


def test_sqltable_reload_reads_back_rows(simple_dbproxy):
    """Seed rows via core insert, then let SqlTable reload/read them.

    DbProxy sessions run in legacy autocommit mode (proxy.py: autocommit=True),
    so we seed via the engine to avoid 'No transaction is begun.'  SqlTable
    then loads through its own session.
    """
    from sqlkit.widgets import SqlTable

    Simple, db = simple_dbproxy
    table = Simple.__table__
    with db.metadata.bind.begin() as conn:
        conn.execute(table.insert(), [
            {"name": "a", "qty": 1},
            {"name": "b", "qty": 2},
        ])

    st = SqlTable(Simple, dbproxy=db, show=False)
    st.reload()
    names = {row.name for row in st.records}
    assert names == {"a", "b"}
