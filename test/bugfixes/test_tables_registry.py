"""TableDescr(register=False) must not wipe the global description registry.

The old code declared ``global tables`` inside ``__init__``: the declaration
applies to the whole function, so the ``register=False`` branch rebound the
module-level ``tables`` registry to a plain dict, losing every registered
description and breaking the ``Tables.__getitem__`` fallback.
"""

import sqlalchemy as sa

from sqlkit.db import utils
from sqlkit.db.utils import MissingMetadata, Tables, TableDescr


def _make_table(name):
    md = sa.MetaData()
    table = sa.Table(
        name, md,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(32)),
    )
    md.bind = sa.create_engine('sqlite://')
    md.create_all(md.bind)
    return table, md


def test_register_false_does_not_clobber_global_registry():
    table, md = _make_table('regfilms')
    TableDescr(table, format='%(title)s', metadata=md)
    assert isinstance(utils.tables, Tables)

    TableDescr(table, format='%(title)s', metadata=md, register=False)
    assert isinstance(utils.tables, Tables)
    # the previously registered description is still there
    assert utils.tables['regfilms'].format == '%(title)s'


def test_register_false_does_not_register():
    table, md = _make_table('regfilms_throwaway')
    TableDescr(table, format='%(title)s', metadata=md, register=False)
    try:
        utils.tables['regfilms_throwaway']
    except MissingMetadata:
        pass
    else:
        raise AssertionError('register=False must not register the description')


def test_unknown_table_raises_missing_metadata():
    try:
        Tables()['no_such_table_anywhere']
    except MissingMetadata:
        pass
    else:
        raise AssertionError('expected MissingMetadata')
