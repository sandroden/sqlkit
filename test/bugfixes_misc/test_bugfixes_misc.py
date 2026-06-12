"""
Headless regression tests for the targeted code-review bugfixes.

These tests are self-contained and avoid creating real GTK widgets where
possible. They cover:

* fix 1  -- misc/babel_support.py imports cleanly even with locale forced to C
* fix 9  -- layout.widgets.register() really binds the class into module globals
* fix 10 -- layout.dateedit.DateEdit.get_datetime() checks new_time (not new_date)
* fix 13 -- layout.image_widget uses .props.visible (no 'pros.visibile' typo)
* fix 17 -- debug.trace_function() compiles the *include* pattern
"""
import importlib

import pytest


# --------------------------------------------------------------------------
# fix 1: babel_support imports with locale forced to 'C'
# --------------------------------------------------------------------------
def test_babel_support_imports_with_C_locale(monkeypatch):
    # Force a 'C'-like environment so the reload branch (which uses importlib)
    # is exercised. Before the fix importlib was used before being imported.
    monkeypatch.setenv("LANG", "C")
    monkeypatch.setenv("LC_NUMERIC", "C")
    monkeypatch.setenv("LC_TIME", "C")

    import sqlkit.misc.babel_support as bs

    # reload to actually re-run module top-level code under the forced env
    importlib.reload(bs)

    # module exposes babel's numbers/dates after a successful import
    assert hasattr(bs, "numbers")
    assert hasattr(bs, "dates")
    assert hasattr(bs, "importlib")


# --------------------------------------------------------------------------
# fix 9: register() binds the class name into the widgets module globals
# --------------------------------------------------------------------------
def test_register_binds_class_into_module_globals():
    from sqlkit.layout import widgets

    class MyDummyWidgetForTest:
        # register() only reads __name__; nothing else is required here
        pass

    mod_name = "dummy_alias_for_test"
    # ensure a clean slate
    widgets._W.pop(mod_name, None)
    widgets.__dict__.pop("MyDummyWidgetForTest", None)

    widgets.register(MyDummyWidgetForTest, mod_name, force=True)

    # In Py3 exec("global X") did NOT touch module globals; the fix uses
    # globals()[name] = Class, so the name must now live in the module dict.
    assert widgets.__dict__.get("MyDummyWidgetForTest") is MyDummyWidgetForTest
    assert widgets._W[mod_name] is MyDummyWidgetForTest

    # cleanup
    widgets._W.pop(mod_name, None)
    widgets.__dict__.pop("MyDummyWidgetForTest", None)


# --------------------------------------------------------------------------
# fix 10: get_datetime returns the *time* error string when get_time() fails
# --------------------------------------------------------------------------
def test_get_datetime_propagates_time_error():
    import datetime

    from sqlkit.layout.dateedit import DateTimeEdit

    class FakeEdit:
        """Minimal stand-in exposing only what get_datetime() touches."""
        def __init__(self, date_val, time_val):
            self._date = date_val
            self._time = time_val

        def get_date(self):
            return self._date

        def get_time(self):
            return self._time

    # Call the unbound method to avoid instantiating a real Gtk.Box.
    get_datetime = DateTimeEdit.get_datetime

    # date OK, time is an error string -> must return the time error string.
    fake = FakeEdit(datetime.date(2020, 1, 2), "BAD-TIME")
    assert get_datetime(fake) == "BAD-TIME"

    # date is an error string -> returns the date error string (unchanged).
    fake = FakeEdit("BAD-DATE", datetime.time(10, 0))
    assert get_datetime(fake) == "BAD-DATE"

    # both valid -> a real datetime is built.
    fake = FakeEdit(datetime.date(2020, 1, 2), datetime.time(10, 30))
    result = get_datetime(fake)
    assert isinstance(result, datetime.datetime)
    assert result == datetime.datetime(2020, 1, 2, 10, 30)


# --------------------------------------------------------------------------
# fix 13: the image_widget source uses .props.visible (no double typo)
# --------------------------------------------------------------------------
def test_image_widget_uses_props_visible():
    import inspect

    from sqlkit.layout import image_widget

    src = inspect.getsource(image_widget)
    assert "pros.visibile" not in src
    assert "self.status_bar.props.visible = value" in src


# --------------------------------------------------------------------------
# fix 17: trace_function compiles the include pattern (not exclude)
# --------------------------------------------------------------------------
def test_trace_function_sets_include_pattern():
    from sqlkit.debug import debug

    debug.trace_function(include="^only_this$")

    assert debug.FUNCTION_INCLUDE is not None
    # the compiled pattern must be the *include* argument
    assert debug.FUNCTION_INCLUDE.pattern == "^only_this$"
    assert debug.FUNCTION_INCLUDE.match("only_this")
    assert not debug.FUNCTION_INCLUDE.match("something_else")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
