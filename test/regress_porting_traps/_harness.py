"""Tiny test harness used by the regress_porting_traps scripts.

Pytest is not installed in the venv; instead each script defines test_*
functions and calls run_tests(globals()) in __main__. The harness reports
counts and exits with non-zero on any failure.
"""
import os
import sys
import traceback


def run_tests(ns, name=None):
    name = name or ns.get("__name__", "tests")
    tests = sorted(
        (n, fn) for n, fn in ns.items()
        if n.startswith("test_") and callable(fn)
    )
    passed = 0
    failed = 0
    failures = []
    print("=== %s: %d tests ===" % (name, len(tests)))
    for tname, fn in tests:
        try:
            fn()
        except Exception as e:
            failed += 1
            failures.append((tname, e, traceback.format_exc()))
            print("  FAIL  %s: %s" % (tname, e))
        else:
            passed += 1
            print("  PASS  %s" % tname)
    if failed:
        print("\n--- failures ---")
        for tname, _, tb in failures:
            print("\n[%s]" % tname)
            print(tb)
    print("\n=== summary: %d passed, %d failed ===" % (passed, failed))
    return passed, failed


def project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", ".."))


def ensure_path():
    root = project_root()
    if root not in sys.path:
        sys.path.insert(0, root)
