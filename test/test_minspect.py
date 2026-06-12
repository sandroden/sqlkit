"""sqlkit.db.minspect.InspectMapper on a sqlite-backed mapper.

InspectMapper introspects a SQLAlchemy mapper into field metadata:
``field_list``, ``pkeys`` (per table) and per-field dicts with python types.
See test/doctest/mapper_inspect.txt for the historic reference.
"""
import datetime
from decimal import Decimal

import pytest

# InspectMapper is GTK-free (no widgets built here), so no 'gtk' marker.


@pytest.fixture
def info(models):
    from sqlkit.db.minspect import InspectMapper

    return InspectMapper(models.AllTypes.__mapper__)


def test_field_list_contains_all_columns(info):
    expected = {
        "id",
        "varchar10",
        "integer",
        "date",
        "datetime",
        "numeric",
        "bool",
        "bool_null",
        "text",
    }
    assert expected <= set(info.field_list)


def test_pkeys(info):
    assert info.pkeys == {"all_types": ["id"]}


def test_get_pkeys(info):
    assert info.get_pkeys("all_types") == ["id"]


@pytest.mark.parametrize(
    "name, py_type",
    [
        ("integer", int),
        ("varchar10", str),
        ("date", datetime.date),
        ("datetime", datetime.datetime),
        ("numeric", Decimal),
        ("bool", bool),
    ],
)
def test_python_types(info, name, py_type):
    assert info.fields[name]["type"] is py_type


def test_field_attrs_basic_metadata(info):
    attrs = info.fields["varchar10"]
    assert attrs["table_name"] == "all_types"
    assert attrs["nullable"] is False
    assert attrs["pkey"] is False
    assert attrs["length"] == 10
    assert attrs["col"].name == "varchar10"


def test_id_is_pkey(info):
    assert info.fields["id"]["pkey"] is True


def test_contains_and_len(info):
    assert "integer" in info
    assert "nope" not in info
    assert len(info) == len(info.field_list)


def test_field_dicts_via_fields_container(info):
    # Both info.fields[name] and info[name] reach the field dict.
    assert info.fields["integer"]["table_name"] == "all_types"


def test_getitem_and_table_fields(info):
    """``__getitem__`` and ``table_fields`` return field metadata.

    Field dicts are stored in ``self.fields`` (a Container).  The original
    design stored them directly on the InspectMapper instance, so
    ``__getitem__`` did ``getattr(self, item)``; when storage moved to
    ``self.fields`` the lookup was never updated and ``info[name]`` (plus
    ``table_fields`` / ``prop_fields`` built on it) broke.  __getitem__ now
    looks the dict up in ``self.fields``, restoring the original semantics.
    """
    assert info["integer"]["table_name"] == "all_types"
    assert info["integer"] is info.fields["integer"]
    assert set(info.table_fields("all_types")) == set(info.field_list)


def test_foreign_key_column_detected(models):
    """FK detection at the *column* level."""
    from sqlalchemy import Column, ForeignKey, Integer, String
    from sqlalchemy.orm import declarative_base

    from sqlkit.db.minspect import InspectMapper

    Base = declarative_base()

    class Reg(Base):
        __tablename__ = "reg_norel"
        id = Column(Integer, primary_key=True)

    class Fl(Base):
        __tablename__ = "fl_norel"
        id = Column(Integer, primary_key=True)
        year = Column(Integer)
        reg_id = Column(Integer, ForeignKey("reg_norel.id"))

    info = InspectMapper(Fl.__mapper__)
    assert info.fields["reg_id"]["fkey"]
    assert info.is_fkey("reg_id")
    assert not info.fields["year"]["fkey"]


def test_minspect_handles_relationship_property(models):
    """A mapper with relationship props is introspected without crashing.

    ``_add_loader_field`` looks up ``mapper.c[<relation_key>]`` to read the
    column length; a relationship key is not a column, so that lookup raises
    KeyError.  The py2 original caught it with a bare ``except:`` (length=None);
    the porting narrowed the except and dropped KeyError, making InspectMapper
    crash on any relationship.  KeyError is caught again, so this now works and
    the relationship is registered as a *loader* field.
    """
    from sqlkit.db.minspect import InspectMapper

    info = InspectMapper(models.Film.__mapper__)
    assert "regista" in info.field_list
    assert info.is_loader("regista")
    # the loader carries no column length and is editable metadata
    assert info.fields["regista"]["length"] is None
    # plain columns still introspect correctly alongside the relationship
    assert info.fields["title"]["table_name"] == "films"
    assert info.is_fkey("regista_id")
