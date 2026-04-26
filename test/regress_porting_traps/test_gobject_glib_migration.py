"""Trap: GObject.{idle_add,timeout_add,source_remove,markup_escape_text}
emit PyGIDeprecationWarning. Migrate to GLib.*.

Fixed in 22 occurrences across 8 files (commit 1854). This grep test
catches any regression — i.e. any new code that re-introduces the
deprecated `GObject.<one of those>` pattern.
"""
import os
import re

from _harness import ensure_path, project_root, run_tests
ensure_path()


DEPRECATED_NAMES = ("idle_add", "timeout_add", "source_remove", "markup_escape_text")


def _walk_py(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # skip hidden, build, egg-info, venv
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in (
                           "build", "dist", "__pycache__",
                           "sqlkit.egg-info", ".venv")]
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def test_no_gobject_glib_calls_remain():
    """Search the whole sqlkit/ tree for `GObject.<deprecated>` usage."""
    pat = re.compile(r"\bGObject\.(%s)\b" % "|".join(DEPRECATED_NAMES))
    sqlkit_dir = os.path.join(project_root(), "sqlkit")
    offenders = []
    for path in _walk_py(sqlkit_dir):
        with open(path, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                # tolerate comments/strings that talk about the pattern
                stripped = line.split("#", 1)[0]
                if pat.search(stripped):
                    offenders.append("%s:%d: %s" % (path, i, line.rstrip()))
    assert not offenders, (
        "Deprecated GObject.* calls found (must be GLib.*):\n  " +
        "\n  ".join(offenders))


if __name__ == "__main__":
    import sys
    p, f = run_tests(globals(), "test_gobject_glib_migration")
    sys.exit(0 if f == 0 else 1)
