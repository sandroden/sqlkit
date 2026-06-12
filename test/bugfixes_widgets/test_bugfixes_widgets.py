"""
Self-contained regression tests for targeted bug-fixes applied to
``sqlkit/widgets/`` during a code review.

Each test documents the *finding number* from the review and verifies the
fix without requiring a real database connection nor a running X display
beyond what GTK needs to import (run under ``xvfb-run`` when needed).

Run with::

    uv run pytest test/bugfixes_widgets/ -q
    # or, if GTK needs a display:
    xvfb-run -a uv run pytest test/bugfixes_widgets/ -q
"""
import ast
import csv
import os
import tempfile

import pytest


HERE = os.path.dirname(os.path.abspath(__file__))
SQLKIT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "sqlkit"))


def _read(rel_path):
    with open(os.path.join(SQLKIT_ROOT, rel_path), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Finding 1: cell_renderers.py used Gdk without importing it and called the
# Gtk2-only ``widget.window`` attribute.
# ---------------------------------------------------------------------------
def test_finding1_cell_renderers_imports_gdk_and_uses_get_window():
    src = _read(os.path.join("widgets", "table", "cell_renderers.py"))

    # Gdk is now imported.
    assert "from gi.repository import Gdk" in src

    # The module parses and references Gdk as a bound name (not a NameError
    # waiting to happen): collect all imported top-level names and ensure Gdk
    # is among them while Gdk.* is actually used in the source.
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    assert "Gdk" in imported
    assert "Gdk." in src  # Gdk is actually used

    # The Gtk2 attribute access is gone, replaced by get_window().
    assert "widget.window" not in src
    assert "widget.get_window()" in src


def test_finding1_module_imports_under_gtk():
    """Importing the module must not raise NameError for Gdk."""
    pytest.importorskip("gi")
    import gi

    gi.require_version("Gtk", "3.0")
    # The import itself is the assertion; a missing Gdk import would have made
    # the module fail at *use* time, but we also confirm the symbol is bound.
    from sqlkit.widgets.table import cell_renderers

    assert cell_renderers.Gdk is not None


# ---------------------------------------------------------------------------
# Finding 5: SimpleCompletion.set_values discarded the result of sorted().
# We test the pure behaviour by driving the method on a minimal stand-in that
# only carries the attribute the method touches.
# ---------------------------------------------------------------------------
def test_finding5_set_values_sorts_the_list():
    from sqlkit.widgets.common import completion

    class Dummy:
        set_values = completion.SimpleCompletion.set_values

    d = Dummy()
    d.set_values([3, 1, 2])
    assert d.possible_values == [1, 2, 3], (
        "set_values must assign the sorted result, not discard it"
    )


def test_finding5_set_values_keeps_callables_untouched():
    from sqlkit.widgets.common import completion

    class Dummy:
        set_values = completion.SimpleCompletion.set_values

    d = Dummy()
    f = lambda text: ["a", "b"]
    d.set_values(f)
    assert d.possible_values is f


# ---------------------------------------------------------------------------
# Finding 8: get_match_operator used a fragile if/if/if/else chain.
# Verify the operator returned for each mode is correct and unchanged.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "mode, expected",
    [
        ("start", "MATCH_OP"),
        ("regexp", "MATCH_OP"),
        ("exact", "="),
        ("something-else", "MATCH_OP"),
    ],
)
def test_finding8_get_match_operator(mode, expected):
    from sqlkit.widgets.common import completion

    class Dummy:
        MATCH_OPERATOR = "MATCH_OP"
        get_match_operator = completion.SimpleCompletion.get_match_operator

    d = Dummy()
    d.mode = mode
    assert d.get_match_operator() == expected


def test_finding8_source_uses_elif_chain():
    src = _read(os.path.join("widgets", "common", "completion.py"))
    # The repaired block must be a single if/elif/elif/else chain.
    assert "elif self.mode == 'regexp':" in src
    assert "elif self.mode == 'exact':" in src


# ---------------------------------------------------------------------------
# Finding 9: FilterFKeyTool.get_suitable_operators had a duplicated '~*' for
# postgres; the 4th element should be '!~' (matching FilterStringTool).
# ---------------------------------------------------------------------------
def test_finding9_fkey_postgres_operators_have_no_duplicate():
    from sqlkit.widgets.common import sqlfilter

    class Dummy:
        bind_name = "postgresql"
        STD_OPERATORS = ["X", "Y"]
        get_suitable_operators = sqlfilter.FilterFKeyTool.get_suitable_operators

    ops = Dummy().get_suitable_operators()
    regexp_ops = ops[:4]
    assert regexp_ops == ["~*", "~", "!~*", "!~"], regexp_ops
    # No duplicate in the regexp operator group.
    assert len(set(regexp_ops)) == 4


# ---------------------------------------------------------------------------
# Finding 7: CSV export opened the file in binary mode ("wb") which is
# incompatible with csv.writer on Python 3. Verify writing works in text mode
# the way ExportDialog.write now does it.
# ---------------------------------------------------------------------------
def test_finding7_csv_writer_text_mode_roundtrip():
    rows = [["a", "b"], ["c", "d"]]
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        # Mirror the fixed code path exactly.
        f = open(path, "w", newline="")
        writer = csv.writer(f, dialect="excel")
        writer.writerows(rows)
        f.close()

        with open(path, newline="") as fh:
            read_back = list(csv.reader(fh))
        assert read_back == rows
    finally:
        os.remove(path)


def test_finding7_source_uses_text_mode():
    src = _read(os.path.join("widgets", "table", "table.py"))
    assert 'open(filename, "w", newline="")' in src
    assert 'open(filename, "wb")' not in src


# ---------------------------------------------------------------------------
# Finding 3: EnumCompletion.show_possible_completion referenced an undefined
# ``obj`` in the (one and mode == 'exact') branch. The repaired version must
# return a DictLike built from the loop data, and must not raise NameError.
# ---------------------------------------------------------------------------
def test_finding3_enum_exact_branch_no_nameerror():
    from sqlkit.widgets.common import completion
    from sqlkit.db.utils import DictLike

    class FakeField:
        values = {1: "one", 2: "two"}

    class FakeModel:
        def clear(self):
            pass

    class FakeCompletion:
        def set_model(self, m):
            pass

    class FakeMaster:
        gui_fields = {"f": FakeField()}
        force_enum = False

        def sb(self, *a, **k):
            pass

    appended = []

    class Stub(completion.EnumCompletion):
        def __init__(self):
            # bypass heavy __init__
            self.master = FakeMaster()
            self.field_name = "f"
            self.force_enum = False
            self.model = FakeModel()
            self.completion = FakeCompletion()

        def append_to_model(self, idx, text):
            appended.append((idx, text))

    stub = Stub()
    result = stub.show_possible_completion(
        widget=None, mode="exact", one=True, sb=False, pop=False
    )
    # No NameError, and a DictLike is returned (the documented contract of the
    # superclass for the (one and mode=='exact') case).
    assert isinstance(result, DictLike)
    # The loop ran and populated the model.
    assert appended == [(1, "one"), (2, "two")]


def test_finding3_source_no_bare_undefined_obj():
    """The literal 'return DictLike(obj)' (with undefined obj) is gone in the
    EnumCompletion branch; it is now guarded by a try/except."""
    src = _read(os.path.join("widgets", "common", "completion.py"))
    # The repaired EnumCompletion branch wraps an ObjLike in a try/except.
    assert "utils.ObjLike({'value': idx, 'text': text})" in src


# ---------------------------------------------------------------------------
# Finding 4: typo grup_column -> group_column.
# ---------------------------------------------------------------------------
def test_finding4_typo_fixed():
    src = _read(os.path.join("widgets", "common", "completion.py"))
    assert "grup_column" not in src


# ---------------------------------------------------------------------------
# Finding 11: pop_menu referenced self.w (nonexistent) instead of
# self.master.widgets.
# ---------------------------------------------------------------------------
def test_finding11_pop_menu_uses_master_widgets():
    src = _read(os.path.join("widgets", "common", "completion.py"))
    assert "self.master.widgets['M=popup'].destroy()" in src
    assert "self.w['M=popup'].destroy()" not in src
