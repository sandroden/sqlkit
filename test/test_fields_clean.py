"""sqlkit.fields: FieldChooser picks the right Field class and clean_value.

Fields are GObject-derived; instantiating them imports GTK, so these tests
carry the ``gtk`` marker and must run under ``xvfb-run -a``.

A Field is built from a ``field_attrs`` dict produced by InspectMapper
(``info.fields[name]``); see test/doctest/fields.txt for the historic API.
"""
import datetime
from decimal import Decimal

import pytest

pytestmark = pytest.mark.gtk


@pytest.fixture
def field_factory(models, monkeypatch):
    """Return (chooser, make) where make(name) builds the field instance.

    Fields read ``babel.default_locale('LC_NUMERIC'/'LC_TIME')`` at
    instantiation time (fields.py), so numeric/date parsing is locale
    dependent.  We pin the locale to en_US (m/d/y dates, '.' decimal point)
    so the assertions are deterministic regardless of the developer's $LANG.
    """
    for var in ("LC_ALL", "LC_NUMERIC", "LC_TIME", "LANG"):
        monkeypatch.setenv(var, "en_US.UTF-8")

    from sqlkit.db.minspect import InspectMapper
    from sqlkit.fields import FieldChooser

    info = InspectMapper(models.AllTypes.__mapper__)
    chooser = FieldChooser(info, {})

    def make(name):
        attrs = info.fields[name]
        FieldClass = chooser.get_field(name, attrs, name)
        return FieldClass(name, attrs)

    return chooser, make, info


# --------------------------------------------------------------------------- #
# FieldChooser picks the right class from the column type
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name, expected_cls",
    [
        ("varchar10", "VarcharField"),
        ("integer", "IntegerField"),
        ("date", "DateField"),
        ("datetime", "DateTimeField"),
        ("numeric", "DecimalField"),
        ("bool", "BooleanField"),
        ("bool_null", "BooleanNullField"),
        ("text", "TextField"),
    ],
)
def test_field_chooser_picks_class(field_factory, name, expected_cls):
    chooser, _, info = field_factory
    cls = chooser.get_field(name, info.fields[name], name)
    assert cls.__name__ == expected_cls


# --------------------------------------------------------------------------- #
# clean_value
# --------------------------------------------------------------------------- #
def test_varchar_clean_value(field_factory):
    _, make, _ = field_factory
    f = make("varchar10")
    assert f.clean_value("hello") == "hello"


def test_integer_clean_value(field_factory):
    _, make, _ = field_factory
    f = make("integer")
    assert f.clean_value(1) == 1
    cleaned = f.clean_value("42")
    assert cleaned == 42
    assert isinstance(cleaned, int)


def test_date_clean_value(field_factory):
    _, make, _ = field_factory
    f = make("date")
    assert f.clean_value(datetime.date(2008, 6, 2)) == datetime.date(2008, 6, 2)
    # en_US default locale parses m/d/y
    assert f.clean_value("6/2/2008") == datetime.date(2008, 6, 2)


def test_datetime_clean_value(field_factory):
    _, make, _ = field_factory
    f = make("datetime")
    val = datetime.datetime(2008, 6, 2, 15, 30)
    assert f.clean_value(val) == val


def test_decimal_clean_value(field_factory):
    _, make, _ = field_factory
    f = make("numeric")
    assert f.clean_value(Decimal("1.2")) == Decimal("1.2")
    cleaned = f.clean_value("4881.69")
    assert cleaned == Decimal("4881.69")
    assert isinstance(cleaned, Decimal)
    assert f.clean_value(12) == Decimal("12")


def test_boolean_clean_value(field_factory):
    _, make, _ = field_factory
    f = make("bool")
    assert f.clean_value(True) is True
    assert f.clean_value(False) is False
    # None coerced to False for a non-nullable boolean
    assert f.clean_value(None) is False


def test_boolean_clean_value_rejects_non_bool(field_factory):
    from sqlkit.exc import ValidationError

    _, make, _ = field_factory
    f = make("bool")
    with pytest.raises(ValidationError):
        f.clean_value("yes")


def test_boolean_null_allows_none(field_factory):
    _, make, _ = field_factory
    f = make("bool_null")
    assert f.clean_value(None) is None
    assert f.clean_value(True) is True


# --------------------------------------------------------------------------- #
# format_value round-trips to a string
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name, raw", [
    ("integer", "1"),
    ("numeric", "1.2"),
    ("date", "6/2/2008"),
])
def test_format_value_is_string(field_factory, name, raw):
    _, make, _ = field_factory
    f = make(name)
    out = f.format_value(f.clean_value(raw))
    assert isinstance(out, str)
