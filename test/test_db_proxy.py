"""sqlkit.db.proxy.DbProxy on a sqlite in-memory db.

Join syntax (see DbProxy.get_mapper / join_tables docstrings):
  * ``|``  -> inner join
  * ``||`` -> outer join
Tables may be given as a string ("films registi"), a list of Table objects,
or a list with explicit '|' / '||' separators.
"""
import pytest

from sqlkit.db import proxy


# --------------------------------------------------------------------------- #
# get_table
# --------------------------------------------------------------------------- #
def test_get_table_returns_known_table(dbproxy, metadata):
    t = dbproxy.get_table("films")
    assert t is metadata.tables["films"]


def test_get_session(dbproxy):
    sess = dbproxy.get_session()
    assert sess is not None
    # it can run a trivial query
    from sqlalchemy import text

    assert sess.execute(text("select 1")).scalar() == 1


# --------------------------------------------------------------------------- #
# join2tables: inner vs outer
# --------------------------------------------------------------------------- #
def test_join2tables_outer(dbproxy, metadata):
    films, registi = metadata.tables["films"], metadata.tables["registi"]
    j = dbproxy.join2tables(films, registi, mode="outerjoin")
    assert getattr(j, "isouter", False) is True


def test_join2tables_inner(dbproxy, metadata):
    films, registi = metadata.tables["films"], metadata.tables["registi"]
    j = dbproxy.join2tables(films, registi, mode="join")
    assert getattr(j, "isouter", False) is False


# --------------------------------------------------------------------------- #
# join_tables with '|' and '||' separators -> mapper
# --------------------------------------------------------------------------- #
def test_join_tables_single_pipe_inner(dbproxy, metadata):
    films, registi = metadata.tables["films"], metadata.tables["registi"]
    m = dbproxy.join_tables([films, "|", registi])
    assert m.local_table.isouter is False


def test_join_tables_double_pipe_outer(dbproxy, metadata):
    films, registi = metadata.tables["films"], metadata.tables["registi"]
    m = dbproxy.join_tables([films, "||", registi])
    assert m.local_table.isouter is True


# --------------------------------------------------------------------------- #
# get_mapper: string form auto-joins; '||' triggers an outer join
# --------------------------------------------------------------------------- #
def test_get_mapper_single_table_string(dbproxy):
    m = dbproxy.get_mapper(None, "films")
    assert m.local_table.name == "films"


def test_get_mapper_string_inner_join(dbproxy):
    # space-separated string (no pipe token) -> auto inner join, works.
    m = dbproxy.get_mapper(None, "films registi")
    assert m.local_table.isouter is False


@pytest.mark.parametrize("spec", ["films | registi", "films || registi"])
def test_known_bug_get_mapper_string_pipe_separator(dbproxy, spec):
    """Document a bug: '|' / '||' don't work in the *string* form of get_mapper.

    get_mapper inserts spaces around the pipes then splits the string and
    feeds EVERY token to get_table(); the '|' / '||' tokens are looked up as
    table names and raise NoSuchTableError.  The outer/inner-join selection
    only works through the *list* form (see join_tables tests above).
    """
    from sqlalchemy.exc import NoSuchTableError

    with pytest.raises(NoSuchTableError):
        dbproxy.get_mapper(None, spec)


def test_get_mapper_passthrough(dbproxy, metadata):
    sentinel = object()
    assert dbproxy.get_mapper(sentinel, "films") is sentinel


# --------------------------------------------------------------------------- #
# the joined mapper resolves duplicate column names into writable attributes
# (both films.id and registi.id are 'id'); join_tables renames collisions.
# --------------------------------------------------------------------------- #
def test_join_mapper_resolves_duplicate_pk_columns(dbproxy, metadata):
    films, registi = metadata.tables["films"], metadata.tables["registi"]
    m = dbproxy.join_tables([films, "||", registi])
    attrs = set(m.attrs.keys())
    # one of the two 'id' columns keeps the natural name, the other is renamed
    assert "id" in attrs
    renamed = {a for a in attrs if a.startswith("registi_id") or a.startswith("films_id")}
    assert renamed, "expected a renamed colliding id column, got: %s" % sorted(attrs)
