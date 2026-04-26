"""
Regression test for the non-raw-string regex trap.

Py3.12+ emits SyntaxWarning for invalid escape sequences like '\\s', '\\d',
'\\|' in non-raw string literals. The regex still works but the warning
clutters output. Fix: prefix r"...".

Tracked in reference_gtk2_to_gtk3_traps.md ("SyntaxWarning su escape regex
in stringa non-raw").

Two complementary checks:
  1. Importing core sqlkit modules under -W error::SyntaxWarning must not
     raise — guarantees current code is clean.
  2. Static AST scan of sqlkit/ for re.{split,match,search,findall,sub,...}
     calls whose first argument is a non-raw string literal containing
     a regex backslash escape — guards against re-introduction.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
import warnings
from pathlib import Path

from _harness import run_tests

ROOT = Path(__file__).resolve().parents[2]
SQLKIT = ROOT / "sqlkit"

REGEX_BACKSLASH_TOKENS = {
    "\\s", "\\S", "\\d", "\\D", "\\w", "\\W", "\\b", "\\B",
    "\\A", "\\Z", "\\|", "\\(", "\\)", "\\[", "\\]", "\\{", "\\}",
    "\\.", "\\+", "\\*", "\\?", "\\^", "\\$",
}
RE_FUNCS = {"split", "match", "search", "findall", "finditer", "sub", "subn", "fullmatch", "compile"}


def _iter_py_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".venv", "__pycache__", ".hg", "build", "dist")]
        for fn in filenames:
            if fn.endswith(".py"):
                yield Path(dirpath) / fn


def test_no_syntaxwarning_on_fields_import():
    """fields.py used to have re.split('\\s+', ...) — a raw-string fix is in place."""
    sys.path.insert(0, str(ROOT))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", SyntaxWarning)
            for mod_name in ("sqlkit.fields", "sqlkit.db.proxy"):
                if mod_name in sys.modules:
                    del sys.modules[mod_name]
                importlib.import_module(mod_name)
    finally:
        sys.path.remove(str(ROOT))


def test_no_re_call_with_non_raw_escape_literal():
    """AST sweep — flags any re.<func>('...\\s...', ...) where the literal
    is NOT r-prefixed and the *source* contains an unescaped backslash escape
    (single \\) — this is what triggers Py3.12 SyntaxWarning.

    Uses ast.get_source_segment so single-backslash (`\\s`) and double-backslash
    (`\\\\s`, already-escaped) are distinguishable.
    """
    offenders = []
    for path in _iter_py_files(SQLKIT):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr in RE_FUNCS
                    and isinstance(func.value, ast.Name) and func.value.id == "re"):
                continue
            if not node.args:
                continue
            first = node.args[0]
            if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                continue
            seg = ast.get_source_segment(source, first)
            if seg is None:
                continue
            stripped = seg.lstrip()
            if stripped.startswith(("r'", 'r"', "rb'", 'rb"', "br'", 'br"')):
                continue
            for tok in REGEX_BACKSLASH_TOKENS:
                if tok in seg and (tok.replace("\\", "\\\\")) not in seg:
                    rel = path.relative_to(ROOT)
                    offenders.append(f"{rel}:{first.lineno}: re.{func.attr}({seg[:60]}...)")
                    break
    assert not offenders, "non-raw regex literals still present:\n  " + "\n  ".join(offenders)


if __name__ == "__main__":
    passed, failed = run_tests(globals(), name="test_regex_raw_strings")
    sys.exit(0 if failed == 0 else 1)
