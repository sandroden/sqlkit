"""Finding #6: the legacy `select([cols], whereclause)` form is deprecated
in SQLAlchemy 1.4 (RemovedIn20Warning) and removed in 2.0.  The library was
converted to `select(*cols).where(...)` together with a connection-based
execution (instead of the deprecated `metadata.bind.execute`).

This test exercises the real code paths in sqlkit.db.utils that issue those
SELECTs against the _sqlkit_table / _sqlkit_field tables, making sure no
deprecation warning leaks and the queries run on SQLAlchemy 1.4.
"""
import warnings

import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

from sqlkit.db import utils


def _engine_with_sqlkit_tables():
    engine = create_engine('sqlite://')
    md = MetaData()
    Table('_sqlkit_table', md,
          Column('name', String(100), primary_key=True),
          Column('search_field', String(100)),
          Column('format', String(100)))
    Table('_sqlkit_field', md,
          Column('id', Integer, primary_key=True),
          Column('table_name', String(100)),
          Column('name', String(100)),
          Column('description', String(100)),
          Column('help_text', String(100)))
    Table('movie', md,
          Column('id', Integer, primary_key=True),
          Column('title', String(100)))
    md.create_all(engine)
    with engine.connect() as conn:
        conn.execute(md.tables['_sqlkit_table'].insert().values(
            name='movie', search_field='title', format='%(title)s'))
        conn.execute(md.tables['_sqlkit_field'].insert().values(
            id=1, table_name='movie', name='title',
            description='Title', help_text='the title'))
    return engine, md


def test_get_description_from_sqlkit_no_deprecation():
    engine, md = _engine_with_sqlkit_tables()
    md.bind = engine
    movie = md.tables['movie']
    with warnings.catch_warnings():
        warnings.simplefilter('error', sqlalchemy.exc.SADeprecationWarning)
        search_field, fmt = utils.get_description_from_sqlkit(movie)
    assert search_field == 'title'
    assert fmt == '%(title)s'


def test_get_labels_and_tips_no_deprecation():
    engine, md = _engine_with_sqlkit_tables()
    md.bind = engine
    movie = md.tables['movie']
    with warnings.catch_warnings():
        warnings.simplefilter('error', sqlalchemy.exc.SADeprecationWarning)
        descr = utils.get_labels_and_tips_from_sqlkit(movie)
    assert descr['title'] == ('Title', 'the title')
