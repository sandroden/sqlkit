"""sqlkit.db.django_syntax: django-like filter parsing.

django2components returns a 6-tuple:
    (joins, op, op_str, value, col, join_args)
(see django_syntax.django2components docstring).

These tests use the declarative ``models`` fixture (films / registi) bound to
an in-memory sqlite engine.
"""
import pytest

from sqlkit.db import django_syntax as djs


# --------------------------------------------------------------------------- #
# django2components on a Table (single column, no relationships)
# --------------------------------------------------------------------------- #
def test_eq_default_operator(models):
    joins, op, op_str, value, col, join_args = djs.django2components(
        models.Film.__table__, {"title": "ed"}
    )
    assert joins == []
    assert op_str == "eq"
    assert op == "="
    assert value == "ed"
    assert col.name == "title"
    assert join_args is None


def test_icontains(models):
    _, op, op_str, value, col, _ = djs.django2components(
        models.Film.__table__, {"title__icontains": "ed"}
    )
    assert op_str == "icontains"
    assert col.name == "title"


@pytest.mark.parametrize(
    "key, exp_op_str, exp_op",
    [
        ("year__lt", "lt", "<"),
        ("year__gt", "gt", ">"),
        ("year__lte", "lte", "<="),
        ("year__gte", "gte", ">="),
    ],
)
def test_comparison_operators(models, key, exp_op_str, exp_op):
    _, op, op_str, value, col, _ = djs.django2components(
        models.Film.__table__, {key: 5}
    )
    assert op_str == exp_op_str
    assert op == exp_op
    assert value == 5


def test_in_operator(models):
    _, op, op_str, value, col, _ = djs.django2components(
        models.Film.__table__, {"year__in": [3, 4]}
    )
    assert op_str == "in"
    assert op == "IN"
    assert value == [3, 4]


def test_notin_operator(models):
    _, op, op_str, value, col, _ = djs.django2components(
        models.Film.__table__, {"year__notin": [3, 4]}
    )
    assert op_str == "notin"
    assert op == "NOT IN"


def test_null_operator(models):
    # NOTE: the recognised operator is 'null'/'notnull' (NOT django's 'isnull').
    _, op, op_str, value, col, _ = djs.django2components(
        models.Film.__table__, {"year__null": True}
    )
    assert op_str == "null"
    assert op == "IS NULL"
    assert value is True


def test_notnull_operator(models):
    _, op, op_str, value, col, _ = djs.django2components(
        models.Film.__table__, {"year__notnull": True}
    )
    assert op_str == "notnull"
    assert op == "IS NOT NULL"


# --------------------------------------------------------------------------- #
# relationship crossing requires a mapper, not a bare table
# --------------------------------------------------------------------------- #
def test_unknown_token_on_table_raises(models):
    # An unrecognised trailing token is treated as a join path; a bare Table
    # cannot cross relationships -> NotImplementedError.
    with pytest.raises(NotImplementedError):
        djs.django2components(models.Film.__table__, {"regista__last_name": "x"})


# --------------------------------------------------------------------------- #
# DjangoParser / django2query
# --------------------------------------------------------------------------- #
def test_django2query_simple_filter(models):
    q = models.session.query(models.Film)
    q2 = djs.django2query(q, models.Film, title="ed")
    assert "WHERE" in str(q2)


def test_django2query_or_produces_or(models):
    q = models.session.query(models.Film)
    q2 = djs.django2query(q, models.Film.__mapper__, title="ed", year=2000, OR=True)
    assert " OR " in str(q2)


def test_django2query_runs_against_sqlite(models):
    # actually execute, to be sure the produced clause is valid SQL
    q = models.session.query(models.Film)
    q2 = djs.django2query(q, models.Film, year__gte=1965)
    rows = q2.all()
    assert {f.title for f in rows} == {"2001"}


# --------------------------------------------------------------------------- #
# django2sqlalchemy
# --------------------------------------------------------------------------- #
def test_django2sqlalchemy_with_mapper(models):
    clause_list, path = djs.django2sqlalchemy(models.Film.__mapper__, title="ed")
    assert "title" in str(clause_list)


def test_django2sqlalchemy_with_table(models):
    clause_list, path = djs.django2sqlalchemy(models.Film.__table__, title="ed")
    assert "title" in str(clause_list)
