"""Findings #4 and #5: join mode handling in DbProxy.

#4: `mode == 'join'` (no-op) in join_tables when the '|' separator is met.
#5: join2tables checked `mode == 'outer'` while join_tables produced
    'outerjoin', so the outer join (`||`) was never applied.
"""
from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey

from sqlkit.db import proxy


def _make_proxy():
    md = MetaData()
    Table('a', md,
          Column('id', Integer, primary_key=True),
          Column('name', String))
    Table('b', md,
          Column('id', Integer, primary_key=True),
          Column('a_id', Integer, ForeignKey('a.id')),
          Column('label', String))
    return proxy.DbProxy(metadata=md), md


def test_join2tables_outerjoin_mode_applies_outer():
    db, md = _make_proxy()
    a, b = md.tables['a'], md.tables['b']
    j = db.join2tables(a, b, mode='outerjoin')
    # an outer join must be marked isouter
    assert getattr(j, 'isouter', False) is True


def test_join2tables_plain_join_not_outer():
    db, md = _make_proxy()
    a, b = md.tables['a'], md.tables['b']
    j = db.join2tables(a, b, mode='join')
    assert getattr(j, 'isouter', False) is False


def test_join_tables_double_pipe_produces_outer():
    """`||` between two tables must produce an outer join in the mapper."""
    db, md = _make_proxy()
    a, b = md.tables['a'], md.tables['b']
    m = db.join_tables([a, '||', b])
    assert m.local_table.isouter is True


def test_join_tables_single_pipe_produces_inner():
    db, md = _make_proxy()
    a, b = md.tables['a'], md.tables['b']
    m = db.join_tables([a, '|', b])
    assert m.local_table.isouter is False
