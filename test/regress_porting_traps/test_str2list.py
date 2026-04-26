"""Trap: re.split('[ ,]*', s) splits between every char in Py3.7+.

Fixed in sqlkit/misc/utils.py:131 (str2list) by switching to '[ ,]+' and
short-circuiting the empty-input case to []. This test would have caught
the bug.
"""
from _harness import ensure_path, run_tests
ensure_path()

from sqlkit.misc.utils import str2list


def test_single_token_no_split():
    # The original bug: re.split('[ ,]*', 'director_id') -> ['', 'd', 'i', 'r', ...]
    assert str2list("director_id") == ["director_id"], str2list("director_id")


def test_comma_separated():
    assert str2list("a,b,c") == ["a", "b", "c"]


def test_space_separated():
    assert str2list("a b c") == ["a", "b", "c"]


def test_mixed_separators():
    assert str2list("a, b , c") == ["a", "b", "c"]


def test_empty_string_returns_empty_list():
    # Was returning [''] before short-circuit
    assert str2list("") == []


def test_whitespace_only_returns_empty_list():
    assert str2list("   ") == []


def test_passthrough_list():
    assert str2list(["x", "y"]) == ["x", "y"]


def test_passthrough_none():
    assert str2list(None) == []


if __name__ == "__main__":
    import sys
    p, f = run_tests(globals(), "test_str2list")
    sys.exit(0 if f == 0 else 1)
