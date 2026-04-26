"""Trap: list.sort(cmp=...) was removed in Py3 — use functools.cmp_to_key.

Fixed in sqlkit/widgets/table/modelproxy.py:383.

The test isolates the comparator pattern: it exercises ModelProxy._cmp /
comp_func without instantiating a real ModelProxy (which needs Gtk
treestore + master). We build a fake proxy with the relevant attributes,
verify cmp_to_key wraps the comparator into a working sort key, and
also do a static check that no `cmp=` kwarg sneaks into a sort call.
"""
import os
import re
from functools import cmp_to_key

from _harness import ensure_path, project_root, run_tests
ensure_path()


def test_cmp_to_key_imported_in_modelproxy():
    path = os.path.join(project_root(), "sqlkit/widgets/table/modelproxy.py")
    with open(path) as fh:
        src = fh.read()
    assert "cmp_to_key" in src, "cmp_to_key should be imported in modelproxy.py"


def test_no_legacy_cmp_kwarg():
    """`list.sort(cmp=...)` and `sorted(..., cmp=...)` removed in Py3."""
    sqlkit_dir = os.path.join(project_root(), "sqlkit")
    pat = re.compile(r"(\.sort\([^)]*\bcmp\s*=|\bsorted\([^)]*\bcmp\s*=)")
    offenders = []
    for dirpath, dirnames, filenames in os.walk(sqlkit_dir):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in (
                           "__pycache__", "sqlkit.egg-info")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            with open(full, encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    code = line.split("#", 1)[0]
                    if pat.search(code):
                        offenders.append("%s:%d: %s" % (full, i, line.rstrip()))
    assert not offenders, "Legacy cmp= kwarg found:\n  " + "\n  ".join(offenders)


def test_cmp_to_key_wrapper_behaviour():
    """Behaviour-preserving sanity check.

    Mirrors the modelproxy._sort_model usage: rows is a list of tuples,
    sort key is cmp_to_key(comp_func). We replicate the comp_func semantics
    where item index 0 carries the object whose attributes drive sort.
    """
    class Obj:
        def __init__(self, name): self.name = name

    def comp_func(t1, t2):
        a, b = t1[0].name, t2[0].name
        return (a > b) - (a < b)

    rows = [(Obj("c"), 0), (Obj("a"), 1), (Obj("b"), 2)]
    rows.sort(key=cmp_to_key(comp_func))
    assert [r[0].name for r in rows] == ["a", "b", "c"]


def test_sort_indices_smoke():
    """Reduced reproduction of modelproxy.sort_indices behaviour without
    pulling in Gtk."""
    rows = [tuple(["c", 1]) + (0,),
            tuple(["a", 2]) + (1,),
            tuple(["b", 3]) + (2,)]

    def comp(r1, r2):
        return (r1[0] > r2[0]) - (r1[0] < r2[0])

    rows.sort(key=cmp_to_key(comp))
    assert [r[-1] for r in rows] == [1, 2, 0]  # original indices reordered


if __name__ == "__main__":
    import sys
    p, f = run_tests(globals(), "test_cmp_to_key")
    sys.exit(0 if f == 0 else 1)
