"""Finding #9: TableDescr.guess_description left `field_name` unbound when the
table had no columns at all, raising NameError instead of returning a sensible
(None, format) tuple.  Initialising field_name=None before the loop fixes it
without changing behaviour for tables that do have columns.
"""
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

from sqlkit.db import utils


def _bind(md):
    engine = create_engine('sqlite://')
    md.bind = engine
    return engine


def test_guess_description_picks_first_string_column():
    md = MetaData()
    t = Table('person', md,
              Column('id', Integer, primary_key=True),
              Column('name', String(50)))
    _bind(md)
    md.create_all(md.bind)
    descr = utils.TableDescr(t, register=False)
    # 'name' is the first string-ish column
    assert descr.description == 'name'


def test_guess_description_empty_table_no_nameerror():
    md = MetaData()
    # a table with no columns is illegal in real DBs, but guess_description
    # iterates over table.c.keys(): we simulate the "no string column" path
    # with a column-less reflected-like Table object.
    t = Table('empty', md)
    _bind(md)
    descr = object.__new__(utils.TableDescr)
    descr.table = t
    descr.metadata = md
    descr.table_name = 'empty'
    # must not raise NameError; with no columns description stays None
    description, fmt = descr.guess_description()
    assert description is None
