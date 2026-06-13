"""Trap: SA 2.0 + psycopg3 reject ``boolean = $1::VARCHAR``.

Legacy filters passed string booleans (``active='t'``) for Boolean columns.
With psycopg2 PostgreSQL coerced the text literal implicitly; psycopg3 sends
typed parameters and ``col.op('=')(value)`` types the bind from the Python
value (str -> VARCHAR), so PostgreSQL raises
``operator does not exist: boolean = character varying``.

Fix: DjangoParser coerces string booleans to real bools when the column is a
Boolean. We verify here, against an in-memory sqlite engine, that:
  1. the bind parameter becomes a real ``bool`` (not the string 't')
  2. the compiled SQL carries no ``::VARCHAR`` cast on the boolean comparison
  3. non-Boolean string columns are left untouched
"""
from _harness import ensure_path, run_tests
ensure_path()


def _build():
    from sqlalchemy import Column, Integer, String, Boolean, create_engine
    from sqlalchemy.orm import declarative_base, Session

    Base = declarative_base()

    class Phase(Base):
        __tablename__ = "job_phase"
        id = Column(Integer, primary_key=True)
        descr = Column(String)
        active = Column(Boolean)
        job_code = Column(String)

    eng = create_engine("sqlite:///:memory:")
    return Phase, Session(eng)


def test_string_t_coerced_to_true():
    from sqlkit.db.django_syntax import django2query
    Phase, session = _build()
    q = django2query(session.query(Phase.id), Phase.__mapper__, active="t")
    params = q.statement.compile().params
    assert params["active_1"] is True, (
        "string 't' must coerce to real bool True, got %r" % (params["active_1"],))


def test_string_f_coerced_to_false():
    from sqlkit.db.django_syntax import django2query
    Phase, session = _build()
    q = django2query(session.query(Phase.id), Phase.__mapper__, active="false")
    params = q.statement.compile().params
    assert params["active_1"] is False, (
        "string 'false' must coerce to real bool False, got %r" % (params["active_1"],))


def test_no_varchar_cast_on_boolean():
    from sqlalchemy.dialects import postgresql
    from sqlkit.db.django_syntax import django2query
    Phase, session = _build()
    q = django2query(session.query(Phase.id), Phase.__mapper__, active="t")
    sql = str(q.statement.compile(dialect=postgresql.dialect()))
    assert "::VARCHAR" not in sql.upper(), (
        "boolean comparison must not be cast to VARCHAR:\n%s" % sql)


def test_real_bool_still_works():
    from sqlkit.db.django_syntax import django2query
    Phase, session = _build()
    q = django2query(session.query(Phase.id), Phase.__mapper__, active=True)
    params = q.statement.compile().params
    assert params["active_1"] is True


def test_string_column_not_touched():
    """A varchar column must keep its string value (e.g. job_code='DIARIO')."""
    from sqlkit.db.django_syntax import django2query
    Phase, session = _build()
    q = django2query(session.query(Phase.id), Phase.__mapper__, job_code="DIARIO")
    params = q.statement.compile().params
    assert params["job_code_1"] == "DIARIO"


if __name__ == "__main__":
    import sys
    p, f, s = run_tests(globals(), "test_django_syntax_boolean_coerce")
    sys.exit(0 if f == 0 else 1)
