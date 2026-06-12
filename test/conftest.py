"""Shared pytest fixtures for the organic sqlkit test suite.

Design notes / constraints:

* This conftest lives in ``test/`` and is the root conftest for the pytest
  collection.  It must NOT break the self-contained suites already present
  (``test/bugfixes``, ``test/bugfixes_widgets``, ``test/bugfixes_misc``): for
  that reason there is **no autouse fixture** here and no ``sys.path``
  manipulation that could shadow their imports.  Everything is opt-in via
  explicit fixture arguments.

* The legacy harnesses (``test/regress_porting_traps`` and ``test/doctest``)
  are excluded from pytest collection in ``pytest.ini`` (``norecursedirs``),
  they keep their own runners.

The fixtures build a minimal SQLAlchemy 1.4 schema (sqlite in-memory) with
``registi`` (directors) and ``films`` (FK to registi) plus an ``all_types``
table covering varchar / int / date / datetime / numeric / bool / text, so
that the field/inspect/proxy tests can exercise several column types without
depending on the demo models under ``demo/sql``.
"""
import datetime
from decimal import Decimal

import pytest


# --------------------------------------------------------------------------- #
# Global-state hygiene (autouse, but strictly a *repair*, never a teardown of
# anything a test legitimately set up).
#
# sqlkit.db.utils keeps a module-level ``tables`` registry that is a
# ``Tables()`` (a Container subclass with a dict-like __getitem__ fallback).
# A pre-existing bug in ``TableDescr.__init__`` (utils.py: the
# ``register=False`` branch) ends up rebinding the module global ``tables`` to
# a plain ``{}``; once that happens, every later ``tables[name]`` lookup raises
# KeyError instead of going through the Tables fallback, breaking unrelated
# tests (e.g. SqlMask/SqlTable construction).  test/bugfixes/test_guess_
# description.py triggers exactly this.
#
# We cannot patch sqlkit/, so this autouse fixture restores a healthy
# ``Tables()`` object *after* each test IF (and only if) it was clobbered into
# a non-Tables object.  It never removes legitimately registered descriptions
# and is therefore harmless to the self-contained bugfix suites.
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _heal_tables_registry():
    yield
    try:
        from sqlkit.db import utils
    except Exception:
        return
    if not isinstance(getattr(utils, "tables", None), utils.Tables):
        utils.tables = utils.Tables()
import os

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.orm import sessionmaker


# --------------------------------------------------------------------------- #
# Backend selection
#
# By default the suite runs on a private sqlite in-memory engine, so behaviour
# is unchanged when SQLKIT_TEST_DB_URL is *not* set.
#
# When SQLKIT_TEST_DB_URL is set (e.g. a PostgreSQL URL) the engine/models
# fixtures bind to that URL instead.  The target database is *shared* across
# runs, so every fixture that creates tables drops them first and again in
# teardown (drop_all / create_all).  The three test tables (registi, films,
# all_types) live in their own metadata, so drop_all only touches them.
# --------------------------------------------------------------------------- #
def _backend_url():
    return os.environ.get("SQLKIT_TEST_DB_URL") or "sqlite://"


def _make_engine():
    url = _backend_url()
    # sqlite in-memory must keep a single connection for the schema to persist;
    # the default behaviour is fine here because each fixture builds its own
    # engine and creates the schema on it.
    return create_engine(url)


def drop_schema(metadata):
    """Drop ``metadata``'s tables on the configured backend.

    sqlite (default): a plain drop_all on a throwaway engine.

    Shared backend (PG via SQLKIT_TEST_DB_URL): the GTK widgets keep DbProxy
    sessions alive for the whole test; on SA2 a session that issued a SELECT
    leaves its connection "idle in transaction", holding a lock that would make
    DROP block forever.  Those connections are checked *out* of their engine's
    pool, so ``engine.dispose()`` cannot close them.  Since the test database
    is dedicated to the suite, we terminate every other backend on it before
    issuing the DROP.  Safe: it never touches other databases of the cluster.
    """
    url = _backend_url()
    eng = create_engine(url)
    if url != "sqlite://":
        from sqlalchemy import text

        # ``engine.begin()`` works identically on SA 1.4 and 2.x (commits on
        # exit); a bare ``connect()`` + ``conn.commit()`` would fail on 1.4
        # where Connection has no commit-as-you-go ``commit()``.
        with eng.begin() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = current_database() "
                    "AND pid <> pg_backend_pid()"
                )
            )
    metadata.drop_all(eng)
    eng.dispose()


# --------------------------------------------------------------------------- #
# date freezing
# --------------------------------------------------------------------------- #
@pytest.fixture
def frozen_date(monkeypatch):
    """Freeze sqlkit.misc.datetools 'today' to 2007-06-02.

    datetools exposes the documented TEST/TODAY mechanism (see
    test/doctest/dates.txt): when ``TEST`` is True, ``today()`` returns
    ``TODAY`` instead of the real date.  We monkeypatch both so the change is
    reverted automatically after the test.

    Returns the frozen ``datetime.date``.
    """
    from sqlkit.misc import datetools as dt

    today = datetime.date(2007, 6, 2)
    monkeypatch.setattr(dt, "TEST", True)
    monkeypatch.setattr(dt, "TODAY", today)
    return today


# --------------------------------------------------------------------------- #
# schema / engine / session
# --------------------------------------------------------------------------- #
@pytest.fixture
def metadata():
    """A fresh MetaData with films / registi (FK) and an all_types table."""
    md = MetaData()
    Table(
        "registi",
        md,
        Column("id", Integer, primary_key=True),
        Column("last_name", String(60), nullable=False),
        Column("nation", String(6)),
    )
    Table(
        "films",
        md,
        Column("id", Integer, primary_key=True),
        Column("title", String(60), nullable=False),
        Column("year", Integer),
        Column("date_release", Date),
        Column("regista_id", Integer, ForeignKey("registi.id"), nullable=False),
    )
    Table(
        "all_types",
        md,
        Column("id", Integer, primary_key=True),
        Column("varchar10", String(10), nullable=False),
        Column("integer", Integer),
        Column("date", Date),
        Column("datetime", DateTime),
        Column("numeric", Numeric(8, 2)),
        Column("bool", Boolean, nullable=False),
        Column("bool_null", Boolean),
        Column("text", Text),
    )
    return md


@pytest.fixture
def engine(metadata):
    """An engine with the schema created and some rows.

    Defaults to sqlite in-memory; binds to ``SQLKIT_TEST_DB_URL`` when set.
    On a shared backend (PG) the test tables are dropped before and after.
    """
    eng = _make_engine()
    metadata.drop_all(eng)
    metadata.create_all(eng)
    registi = metadata.tables["registi"]
    films = metadata.tables["films"]
    with eng.begin() as conn:
        conn.execute(
            registi.insert(),
            [
                {"id": 1, "last_name": "Fellini", "nation": "IT"},
                {"id": 2, "last_name": "Kubrick", "nation": "US"},
            ],
        )
        conn.execute(
            films.insert(),
            [
                {
                    "id": 1,
                    "title": "La dolce vita",
                    "year": 1960,
                    "date_release": datetime.date(1960, 2, 5),
                    "regista_id": 1,
                },
                {
                    "id": 2,
                    "title": "2001",
                    "year": 1968,
                    "date_release": datetime.date(1968, 4, 2),
                    "regista_id": 2,
                },
            ],
        )
    yield eng
    # Shared backends (PG): clean up so the next run starts fresh.
    eng.dispose()
    drop_schema(metadata)


@pytest.fixture
def session(engine):
    """A SQLAlchemy 1.4 session bound to the in-memory engine."""
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


@pytest.fixture
def dbproxy(engine, metadata):
    """A DbProxy bound to the in-memory engine and shared metadata."""
    from sqlkit.db import proxy

    return proxy.DbProxy(engine=engine, metadata=metadata)


# --------------------------------------------------------------------------- #
# declarative mapped models (films / registi / all_types) on the same engine
# --------------------------------------------------------------------------- #
@pytest.fixture
def models(engine):
    """Declarative Regista / Film / AllTypes mapped on the in-memory engine.

    Returns a small namespace object with ``.Regista``, ``.Film``,
    ``.AllTypes`` and ``.session``.  Used by the InspectMapper / GTK smoke
    tests which need real mappers.
    """
    from sqlalchemy.orm import declarative_base, relationship

    Base = declarative_base()

    class Regista(Base):
        __tablename__ = "registi"
        id = Column(Integer, primary_key=True)
        last_name = Column(String(60), nullable=False)
        nation = Column(String(6))

        def __str__(self):
            return self.last_name or ""

    class Film(Base):
        __tablename__ = "films"
        id = Column(Integer, primary_key=True)
        title = Column(String(60), nullable=False)
        year = Column(Integer)
        date_release = Column(Date)
        regista_id = Column(Integer, ForeignKey("registi.id"), nullable=False)
        regista = relationship("Regista", backref="films")

        def __str__(self):
            return self.title or ""

    class AllTypes(Base):
        __tablename__ = "all_types"
        id = Column(Integer, primary_key=True)
        varchar10 = Column(String(10), nullable=False)
        integer = Column(Integer)
        date = Column(Date)
        datetime = Column(DateTime)
        numeric = Column(Numeric(8, 2))
        bool = Column(Boolean, nullable=False)
        bool_null = Column(Boolean)
        text = Column(Text)

    # The ``engine`` fixture already created registi/films/all_types (and will
    # drop them in its own teardown).  create_all is checkfirst by default, so
    # this is a no-op on a shared backend and a real create on sqlite.
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker

    sess = sessionmaker(bind=engine)()

    class _NS:
        pass

    ns = _NS()
    ns.Regista = Regista
    ns.Film = Film
    ns.AllTypes = AllTypes
    ns.session = sess
    ns.Base = Base
    ns.Decimal = Decimal
    yield ns
    sess.close()
