"""Trap: Gtk.TreePath is not hashable in GTK3.

Fixed in sqlkit/widgets/common/completion.py by stringifying via
.to_string() at every match_dict read/write.

The test:
  1. confirms a real Gtk.TreePath is NOT directly hashable
  2. confirms .to_string() produces a stable str usable as dict key
  3. greps completion.py to assert no remaining `match_dict[<...>]`
     usage that bypasses to_string()/get_indices() — defense in depth
"""
import os
import re

from _harness import ensure_path, project_root, run_tests
ensure_path()

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def test_treepath_not_hashable():
    p = Gtk.TreePath.new_from_string("0:2:1")
    try:
        hash(p)
    except TypeError:
        return  # expected
    raise AssertionError(
        "Gtk.TreePath unexpectedly became hashable — does the workaround "
        "in completion.py still need to exist? Re-evaluate.")


def test_treepath_to_string_stable():
    p1 = Gtk.TreePath.new_from_string("0:2:1")
    p2 = Gtk.TreePath.new_from_string("0:2:1")
    assert p1.to_string() == p2.to_string() == "0:2:1"
    # Keys are interchangeable across recreations of the same path
    d = {p1.to_string(): "x"}
    assert d.get(p2.to_string()) == "x"


def test_completion_does_not_key_match_dict_with_raw_treepath():
    """Static check: completion.py never keys match_dict with the raw
    return of get_path() (a Gtk.TreePath). It must call .to_string() or
    .get_indices() at the read/write site, OR assign the stringified
    form to a `path` variable that's used later.
    """
    path = os.path.join(project_root(), "sqlkit/widgets/common/completion.py")
    with open(path) as fh:
        src = fh.read()
    bad = []
    # Pattern: match_dict[...get_path(...)...] without .to_string() / .get_indices()
    raw_pat = re.compile(r"match_dict\[[^\]]*\.get_path\([^\]]*\]")
    safe_pat = re.compile(r"\.(to_string|get_indices)\(")
    for i, line in enumerate(src.splitlines(), 1):
        if not raw_pat.search(line):
            continue
        if safe_pat.search(line):
            continue
        bad.append((i, line.strip()))
    assert not bad, (
        "match_dict keyed by raw Gtk.TreePath (unhashable): %r" % bad)


def test_completion_assigns_path_via_to_string():
    """Whenever completion.py extracts a path via get_path(), it should
    immediately convert via .to_string() or .get_indices() before storing
    it into a variable used as a dict key."""
    path = os.path.join(project_root(), "sqlkit/widgets/common/completion.py")
    with open(path) as fh:
        src = fh.read()
    # Every `path = ... .get_path(...)` line should chain to_string/get_indices
    bad = []
    pat = re.compile(r"^\s*path\s*=\s*.*\.get_path\(")
    safe_pat = re.compile(r"\.(to_string|get_indices)\(")
    for i, line in enumerate(src.splitlines(), 1):
        if pat.search(line) and not safe_pat.search(line):
            bad.append((i, line.strip()))
    assert not bad, (
        "completion.py: path assigned from raw get_path() (unhashable): %r" %
        bad)


if __name__ == "__main__":
    import sys
    p, f = run_tests(globals(), "test_treepath_hashable")
    sys.exit(0 if f == 0 else 1)
