"""Calendar popup positioning: Gdk.Window.get_origin() unpacking (static guard).

GTK3's ``Gdk.Window.get_origin()`` returns a 3-tuple ``(ok, x, y)`` whereas the
GTK2/PyGTK API returned ``(x, y)``.  ``pygi-convert.sh`` renamed
``widget.window`` -> ``widget.get_window()`` but left the 2-value unpacking
``x, y = Gdk.Window.get_origin(...)`` in
``CellEditableCalendar.position_popup``, so opening the date/datetime calendar
popup raised ``ValueError: too many values to unpack``.

This module keeps a *GTK-free* structural guard (no widget import, so it does
not perturb the collection order the legacy GTK smoke suite relies on).  The
matching *runtime* test that actually drives ``position_popup`` lives in
``test/bugfixes_widgets/test_bugfixes_widgets.py``
(``test_finding1_position_popup_unpacks_three_tuple_origin``).
"""
import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(
    os.path.join(HERE, "..", "..", "sqlkit", "widgets", "table", "cell_renderers.py")
)


def test_source_unpacks_origin_success_flag():
    """Every get_origin() assignment unpacks three names (ok, x, y), not two."""
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    # Checked structurally via the AST so substring overlap can't give a false
    # pass (``x, y = ...`` is a substring of ``_ok, x, y = ...``).
    tree = ast.parse(src)
    origin_targets = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            if (
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "get_origin"
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Tuple)
            ):
                origin_targets.append(len(node.targets[0].elts))
    assert origin_targets, "expected an unpacking of Gdk.Window.get_origin(...)"
    assert all(n == 3 for n in origin_targets), (
        "get_origin() must unpack (ok, x, y) — found %r-tuple(s)" % origin_targets
    )
