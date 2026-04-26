"""Trap: Engine.has_table() was deprecated in SA 1.4.

Fixed by switching to sa.inspect(engine).has_table(name). We can't connect
to a real DB here, but we verify:
  1. SA 1.4+ exposes Inspector.has_table on a freshly-built sqlite engine
  2. No source file in sqlkit/ still uses Engine.has_table directly
"""
import os
import re

from _harness import ensure_path, project_root, run_tests
ensure_path()


def test_sa_version_at_least_1_4():
    import sqlalchemy as sa
    major, minor = sa.__version__.split(".")[:2]
    assert (int(major), int(minor)) >= (1, 4), (
        "SA must be >= 1.4 for sa.inspect(engine).has_table to work")


def test_inspect_has_table_on_sqlite():
    import sqlalchemy as sa
    eng = sa.create_engine("sqlite:///:memory:")
    insp = sa.inspect(eng)
    # Must have has_table method
    assert hasattr(insp, "has_table"), "Inspector lacks has_table"
    # And work on an empty DB
    assert insp.has_table("nope") is False


def test_no_engine_dot_has_table_in_source():
    """Static grep: no `<something>.has_table(` where the call site is
    using the engine instance directly (deprecated pattern)."""
    sqlkit_dir = os.path.join(project_root(), "sqlkit")
    # Allow `sa.inspect(...)...has_table(` and `inspect(...)...has_table(`
    # but flag bare `<engine>.has_table(`
    bare_pat = re.compile(r"\bhas_table\(")
    insp_pat = re.compile(r"inspect\([^)]*\)(?:\s*\.\s*[a-zA-Z_]\w*\s*)*\.has_table\(")
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
            for i, line in enumerate(src.splitlines(), 1):
                code = line.split("#", 1)[0]
                if not bare_pat.search(code):
                    continue
                # Skip lines that wrap has_table via inspect(...)
                if insp_pat.search(code):
                    continue
                # Skip definitions / docstrings
                if "def has_table" in code:
                    continue
                offenders.append("%s:%d: %s" % (full, i, line.rstrip()))
    assert not offenders, (
        "Deprecated Engine.has_table() usage found (use sa.inspect):\n  " +
        "\n  ".join(offenders))


if __name__ == "__main__":
    import sys
    p, f = run_tests(globals(), "test_sa_inspect_has_table")
    sys.exit(0 if f == 0 else 1)
