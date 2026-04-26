"""Trap: AppyPod is now the default printing engine in Py3 (was 'ooo').

In Py3 the legacy oootemplate engine cannot run without the `uno` module,
which is no longer available out-of-the-box on recent Ubuntu releases.
Switching the default to 'appy' makes printing usable on a fresh install.

This test guards the new default and pins the public API surface that
clients still depending on oootemplate rely on:

  * ``PRINTING_STYLE`` defaults to ``'appy'``
  * ``set_printing_style`` accepts both ``'appy'`` and ``'ooo'`` and
    rejects everything else
  * the ``oootemplate`` submodule is still importable (we did NOT delete
    it: a customer may still depend on it).
"""
from _harness import ensure_path, run_tests
ensure_path()

from sqlkit.misc import printing


def test_default_is_appy():
    assert printing.PRINTING_STYLE == "appy", printing.PRINTING_STYLE


def test_set_printing_style_appy():
    saved = printing.PRINTING_STYLE
    try:
        printing.set_printing_style("appy")
        assert printing.PRINTING_STYLE == "appy"
    finally:
        printing.set_printing_style(saved)


def test_set_printing_style_ooo():
    saved = printing.PRINTING_STYLE
    try:
        printing.set_printing_style("ooo")
        assert printing.PRINTING_STYLE == "ooo"
    finally:
        printing.set_printing_style(saved)


def test_set_printing_style_rejects_invalid():
    saved = printing.PRINTING_STYLE
    try:
        try:
            printing.set_printing_style("bogus")
        except AssertionError:
            return
        raise AssertionError("set_printing_style('bogus') should have raised")
    finally:
        printing.PRINTING_STYLE = saved


def test_print_tool_classes_both_present():
    # Both engine adapters must remain available: clients can opt back into
    # 'ooo' explicitly via printing_style='ooo' on the SqlWidget.
    assert hasattr(printing, "PrintToolAppy")
    assert hasattr(printing, "PrintToolOoo")


def test_oootemplate_module_still_importable():
    # Regression in the opposite direction: do NOT remove oootemplate.py,
    # at least not yet — a customer's gestionale may still rely on it.
    from sqlkit.misc import oootemplate  # noqa: F401


if __name__ == "__main__":
    run_tests(globals())
