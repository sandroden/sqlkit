#!/usr/bin/env python3
"""Regression smoke test for the Gtk.ActionGroup.add_actions(user_data=tuple)
trap in sqlkit/misc/printing.py around line 484-490.

In PyGTK2, passing user_data=(a, b, c) to add_actions resulted in the callback
being invoked as cb(action, a, b, c) (tuple splatted). PyGObject/GTK3 does NOT
splat the tuple — it passes it as a single argument. The fix wraps the
callback in a closure that splats the tuple at call time.

This test:
  1. Imports sqlkit.misc.printing.PrintTool
  2. Builds a minimal master mock with the needed attrs
  3. Calls add_menu_entry(...) which goes through the closure-binding code
  4. Activates the freshly-added action and asserts the callback receives
     splatted args (template_path is a str — not a tuple)
  5. Stubs get_template to raise a sentinel so we stop before any real I/O

Exit code 0 = fix verified.
Exit code 1 = bug present (TypeError on os.path.split, or wrong arg shape).
"""
import os
import sys
import traceback
from types import SimpleNamespace

# Make sqlkit-gtk3 importable from the project root regardless of cwd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from sqlkit.misc import printing


class SentinelReached(RuntimeError):
    """Raised by the stubbed get_template once the splat passed."""


def make_master():
    """Minimal mock of the master sqlwidget used by PrintTool."""
    ag = Gtk.ActionGroup(name="print")
    ui = Gtk.UIManager()
    ui.insert_action_group(ag, 0)
    ui.add_ui_from_string(
        '<ui><menubar name="Main"><menu action="File">'
        '<menu action="Print"><placeholder name="Print-ph">'
        '<placeholder name="Print"/>'
        '</placeholder></menu></menu></menubar></ui>'
    )
    # The action stubs File/Print parents need to exist:
    parent_ag = Gtk.ActionGroup(name="parents")
    parent_ag.add_actions([
        ("File", None, "File", None, None, None),
        ("Print", None, "Print", None, None, None),
    ])
    ui.insert_action_group(parent_ag, 1)

    master = SimpleNamespace(
        actiongroup_print=ag,
        ui_manager=ui,
        is_mask=lambda: True,
        current=object(),
        records=[],
        related={},
        message=lambda *a, **kw: None,
        nick="testnick",
        dialog=lambda *a, **kw: None,
    )
    return master


def main():
    master = make_master()

    pt = printing.PrintTool(master)
    # Don't auto-add anything: clear template_dir so look_for_automatic_templates is a no-op.
    pt.template_dir = "/nonexistent-template-dir-for-regress"
    pt.disabled = True  # avoid set_visible side effects
    # Replace ObjProxy with a stub that doesn't need master.gui_fields
    pt.obj_proxy_class = lambda obj, master: object()

    # Track what get_template received. We can't propagate exceptions
    # through Gtk's C-level signal dispatch, so use a side-channel dict.
    captured = {"reached": False, "error": None}

    def fake_get_template(template_name, context, server=None, port=None):
        captured["template_name"] = template_name
        captured["server"] = server
        captured["port"] = port
        captured["reached"] = True
        # Raising a sentinel inside a Gtk signal handler gets swallowed
        # (printed to stderr by PyGObject) but doesn't propagate. The
        # side-channel above is what we actually assert against.
        raise SentinelReached("get_template reached with splatted args")

    pt.get_template = fake_get_template
    # Stop before context-ready signal does anything special
    # (it can still emit; default handler is a no-op returning False/None)

    # Use a template_name without a path so split_template_name uses template_dir
    template_name = "myreport.odt"
    description = "Print my report"
    pt.add_menu_entry(description, template_name, mode="pdf",
                      output_name="out.pdf",
                      action_name="templ_myreport_pdf")

    action = master.actiongroup_print.get_action("templ_myreport_pdf")
    assert action is not None, "action was not registered"

    # Now activate. PyGObject swallows Python exceptions thrown inside
    # signal handlers (it just prints them to stderr) — so we rely on
    # the `captured` side-channel to learn whether the splat worked.
    # If the bug is present, `os.path.splitext(os.path.split(...))` runs
    # inside add_menu_entry first (line 474) and explodes BEFORE we ever
    # reach activate. In the post-fix code that line uses template_NAME
    # not template_path, so we should also see captured['reached']=True.
    action.activate()

    if not captured["reached"]:
        print("[FAIL] get_template was never reached — splat likely broken; "
              "look at stderr above for swallowed exception.")
        return 1

    # Verify what get_template got
    tn = captured.get("template_name")
    print("[INFO] get_template received template_name=%r (type=%s)" % (
        tn, type(tn).__name__))
    if not isinstance(tn, str):
        print("[FAIL] template_name should be a str but is %s" % type(tn).__name__)
        return 1
    if "myreport.odt" not in tn:
        print("[FAIL] template_name does not look like the file we passed")
        return 1

    print("[PASS] add_actions splat fix verified — callback received str, not tuple.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
