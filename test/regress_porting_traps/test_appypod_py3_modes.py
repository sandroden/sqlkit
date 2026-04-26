"""Trap: appypod.py uses Py2-style file modes that break on Py3.

Two breakages fixed together:

1. ``NamedTemporaryFile('rwb', ...)`` — Py2 was tolerant of the made-up
   mode 'rwb', Py3's _io.open is strict and raises
   ``ValueError: must have exactly one of create/read/write/append mode``.
   The temp file is only used to obtain ``f.name`` (the actual content is
   written by appy.pod's ``Renderer`` afterwards), so any valid binary
   mode works; we use ``'w+b'`` to preserve the original read/write
   intent of 'rwb'.

2. ``save_as`` did ``open(path, 'w')`` then wrote the bytes returned by
   ``render()`` into it, which in Py3 raises
   ``TypeError: write() argument must be str, not bytes``. The output is
   a binary document (.odt or .pdf), so ``'wb'`` is the right mode.

Static check: read the source and assert the offending strings are gone
and the corrected forms are present. This avoids needing appy.pod's
Renderer (which itself requires LibreOffice/`uno` for .pdf) to run a
true end-to-end render in CI.
"""
import os
import re

from _harness import ensure_path, run_tests
ensure_path()


def _appypod_source():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.normpath(os.path.join(here, "..", ".."))
    with open(os.path.join(root, "sqlkit", "misc", "appypod.py"), encoding="utf-8") as f:
        return f.read()


def test_no_rwb_mode_in_named_temporary_file():
    src = _appypod_source()
    # 'rwb' as a string literal is the Py2-leftover mode that breaks Py3.
    assert "'rwb'" not in src, "Py2-only NamedTemporaryFile mode 'rwb' still in appypod.py"
    assert '"rwb"' not in src


def test_named_temporary_file_uses_valid_binary_mode():
    src = _appypod_source()
    # Must use 'w+b' (or 'wb') — verify the call is binary.
    m = re.search(r"NamedTemporaryFile\((['\"])([^'\"]+)\1", src)
    assert m, "Could not find NamedTemporaryFile call in appypod.py"
    mode = m.group(2)
    assert "b" in mode, f"NamedTemporaryFile mode {mode!r} is not binary"
    valid = {"rb", "wb", "ab", "xb", "r+b", "w+b", "a+b", "x+b"}
    assert mode in valid, f"NamedTemporaryFile mode {mode!r} is not a valid Py3 mode"


def test_save_as_opens_output_in_binary_mode():
    src = _appypod_source()
    # render() returns bytes (line 131: open(output, 'rb').read()), so
    # save_as MUST open the destination in binary mode.
    assert re.search(r"open\(output_path,\s*['\"]wb['\"]\)", src), \
        "save_as must open output_path in binary mode ('wb')"
    assert not re.search(r"open\(output_path,\s*['\"]w['\"]\)", src), \
        "save_as still uses text mode ('w') — render() returns bytes"


if __name__ == "__main__":
    run_tests(globals())
