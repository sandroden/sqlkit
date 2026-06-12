"""sqlkit.misc.utils: Container, DictLike, ObjLike, str2list."""
import pytest

from sqlkit.misc.utils import Container, DictLike, ObjLike, str2list


# --------------------------------------------------------------------------- #
# Container
# --------------------------------------------------------------------------- #
def test_container_init_from_dict_and_access():
    c = Container({"a": 1, "b": 2})
    assert c["a"] == 1
    assert c.b == 2
    assert "a" in c
    assert "z" not in c


def test_container_keys_values_items():
    c = Container()
    c.add_element("x", 10)
    c.add_element("y", 20)
    assert c.keys() == ["x", "y"]
    assert sorted(c.values()) == [10, 20]
    assert dict(c.items()) == {"x": 10, "y": 20}


def test_container_setitem_and_iter_yields_values():
    c = Container()
    c["k"] = "v"
    assert c["k"] == "v"
    # iterating yields values, not keys
    assert list(c) == ["v"]


def test_container_get_default():
    c = Container({"a": 1})
    assert c.get("a") == 1
    assert c.get("missing") is None
    assert c.get("missing", 42) == 42


def test_container_add_element_idempotent_keys():
    c = Container()
    c.add_element("a", 1)
    c.add_element("a", 2)  # re-set same key
    assert c.keys() == ["a"]
    assert c["a"] == 2


# --------------------------------------------------------------------------- #
# DictLike  (used for %(field)s formatting; None -> '')
# --------------------------------------------------------------------------- #
class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_dictlike_lookup_and_none_cast():
    d = DictLike(_Obj(name="bob", age=None))
    assert d["name"] == "bob"
    # None casts to empty string
    assert d["age"] == ""
    # missing attr -> '' (getattr default)
    assert d["nope"] == ""


def test_dictlike_format_string():
    d = DictLike(_Obj(title="hi", subtitle=None))
    assert "%(title)s/%(subtitle)s" % d == "hi/"


# --------------------------------------------------------------------------- #
# ObjLike  (dict keys accessible as attributes)
# --------------------------------------------------------------------------- #
def test_objlike_attribute_access():
    o = ObjLike({"foo": 1, "bar": "baz"})
    assert o.foo == 1
    assert o.bar == "baz"


def test_objlike_missing_key_raises():
    o = ObjLike({"foo": 1})
    with pytest.raises((AttributeError, KeyError)):
        o.missing


# --------------------------------------------------------------------------- #
# str2list
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "value, expected",
    [
        ("a b c", ["a", "b", "c"]),
        ("a, b, c", ["a", "b", "c"]),
        ("a,b ,  c", ["a", "b", "c"]),
        ("  spaced  ", ["spaced"]),
        ("", []),
        ("   ", []),
        (["x", "y"], ["x", "y"]),
        (None, []),
    ],
)
def test_str2list(value, expected):
    assert str2list(value) == expected
