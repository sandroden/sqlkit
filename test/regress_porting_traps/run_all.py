#!/usr/bin/env python3
"""Run every test_*.py in this directory, aggregate pass/fail counts,
exit non-zero if any test fails.

Usage:
  uv run python test/regress_porting_traps/run_all.py
"""
import importlib.util
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _harness import run_tests  # noqa: E402


def load_module(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return name, mod


def main():
    files = sorted(
        os.path.join(HERE, fn) for fn in os.listdir(HERE)
        if fn.startswith("test_") and fn.endswith(".py")
    )
    total_p = total_f = 0
    for path in files:
        name, mod = load_module(path)
        p, f = run_tests(vars(mod), name)
        total_p += p
        total_f += f
        print()
    print("=" * 60)
    print("OVERALL: %d passed, %d failed across %d files" % (
        total_p, total_f, len(files)))
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
