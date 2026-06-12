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
    # The correct way to reach a field dict is info.fields[name].
    # NOTE: info[name] / info.table_fields() are BROKEN for this mapper, see
    # test_known_bug_getitem_and_table_fields below.
    assert info.fields["integer"]["table_name"] == "all_types"


def test_known_bug_getitem_and_table_fields(info):
    """Document a latent bug in InspectMapper.

    InspectMapper.__getitem__ (minspect.py:240) does ``getattr(self, item)``,
    but per-field dicts are stored in ``self.fields`` (a Container), not as
    attributes on the InspectMapper instance.  Therefore ``info[name]`` and
    everything relying on it (``table_fields``, ``prop_fields``) raise
    AttributeError.  Use ``info.fields[name]`` instead.
    """
    with pytest.raises(AttributeError):
        info["integer"]
    with pytest.raises(AttributeError):
        info.table_fields("all_types")


def test_foreign_key_column_detected(models):
    """FK detection at the *column* level.

    A mapper carrying *relationship* properties (e.g. Film.regista) cannot be
    introspected: InspectMapper._add_loader_field crashes at minspect.py:202
    with ``mapper.c[<relation_key>]`` (KeyError).  See
    test_minspect_relationship_property_crashes.  So we build an explicitly
    relationship-free mapper to verify FK metadata of the column.
    """
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


def test_minspect_relationship_property_crashes(models):
    """Regression-lock: a mapper with relationship props is not handled.

    This currently raises KeyError at minspect.py:202.  If sqlkit later fixes
    _add_loader_field this test will fail and should be updated.
    """
    from sqlkit.db.minspect import InspectMapper

    with pytest.raises(KeyError):
        InspectMapper(models.Film.__mapper__)
