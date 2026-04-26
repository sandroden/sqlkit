"""Trap: Gtk.ActionGroup.add_actions(entries, user_data=tuple) does NOT
splat the tuple in PyGObject as PyGTK2 did. Multi-element tuples must
instead be bound to the callback via a closure.

Static check: flag any add_actions(<entries>, <2nd-arg>) call where the
2nd positional/keyword arg is a tuple literal — that is the PyGTK2-style
pattern that breaks at runtime in GTK3.

Single-arg user_data (e.g. a string like 'filter' or 'output') is fine
per the trap notes, so we explicitly only flag tuple literals.
"""
import ast
import os

from _harness import ensure_path, project_root, run_tests
ensure_path()


def _collect_calls(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            yield node


def test_no_add_actions_with_tuple_user_data():
    sqlkit_dir = os.path.join(project_root(), "sqlkit")
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
                src = fh.read()
            try:
                tree = ast.parse(src, filename=full)
            except SyntaxError:
                continue
            for call in _collect_calls(tree):
                attr = getattr(call.func, "attr", None)
                if attr != "add_actions":
                    continue

                # Gather candidate user_data nodes (positional [1] or kw)
                candidates = []
                if len(call.args) >= 2:
                    candidates.append(call.args[1])
                for kw in call.keywords:
                    if kw.arg == "user_data":
                        candidates.append(kw.value)

                for c in candidates:
                    # Tuple literal with >= 2 elements is the broken pattern
                    if isinstance(c, ast.Tuple) and len(c.elts) >= 2:
                        offenders.append(
                            "%s:%d: add_actions(..., <tuple of %d>)" % (
                                full, call.lineno, len(c.elts)))
    assert not offenders, (
        "add_actions called with tuple user_data — won't splat in GTK3:\n  " +
        "\n  ".join(offenders))


def test_printing_uses_closure_not_user_data_tuple():
    """Direct check on the file the original bug lived in."""
    path = os.path.join(project_root(), "sqlkit/misc/printing.py")
    with open(path) as fh:
        src = fh.read()
    # The fix introduced a nested _activate closure binding _td as a default.
    assert "_td=" in src, (
        "printing.py should bind args via a default-arg closure (_td=...)")
    assert "def _activate" in src, (
        "printing.py should define an _activate closure to bypass the "
        "ActionGroup.add_actions tuple-user_data trap")


if __name__ == "__main__":
    import sys
    p, f = run_tests(globals(), "test_add_actions_user_data_tuple")
    sys.exit(0 if f == 0 else 1)
