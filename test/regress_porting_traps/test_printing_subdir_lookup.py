"""Trap: PrintTool.split_template_name used to treat any non-empty
dirname as a complete path, so 'appy/foo.odt' bypassed self.template_dir
and was looked up against the cwd. With the new templates/{appy,oootemplate}/
layout this made AppyPodTemplate fail with "is not the path of a template".

Fix: a relative dirname is now joined under self.template_dir, so
'appy/foo.odt' resolves to template_dir/appy/foo.odt. Absolute paths and
bare filenames keep their previous meaning.
"""
import os

from _harness import ensure_path, run_tests
ensure_path()

from sqlkit.misc import printing


class _FakePrintTool(printing.PrintTool):
    # Bypass __init__ — that needs a Gtk master + actiongroup. We only
    # exercise split_template_name, which only reads self.template_dir.
    def __init__(self, template_dir):
        self.template_dir = template_dir


def _existing_template_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.normpath(os.path.join(here, "..", ".."))
    return os.path.join(root, "demo", "sql", "templates")


def test_subdir_relative_resolved_under_template_dir():
    p = _FakePrintTool(_existing_template_dir())
    dirname, name, path = p.split_template_name("appy/director-movies.odt")
    assert dirname is not None, "subdir lookup returned dirname=None"
    assert dirname.endswith(os.path.join("templates", "appy")), dirname
    assert os.path.isabs(path), path
    assert os.path.exists(path), path


def test_subdir_relative_oootemplate():
    p = _FakePrintTool(_existing_template_dir())
    dirname, name, path = p.split_template_name("oootemplate/movies.odt")
    assert dirname is not None
    assert dirname.endswith(os.path.join("templates", "oootemplate")), dirname
    assert os.path.exists(path), path


def test_bare_filename_still_resolved_under_template_dir():
    # Backward-compat: pre-existing call style 'foo.odt' must still work.
    p = _FakePrintTool(_existing_template_dir())
    dirname, name, path = p.split_template_name("nonexistent.odt")
    # template_dir is set, so dirname starts as template_dir; since the file
    # does not exist split_template_name resets dirname to None — that's the
    # established contract used by use_template().
    assert dirname is None
    assert name == "nonexistent.odt"


def test_absolute_path_unchanged():
    p = _FakePrintTool(_existing_template_dir())
    abs_path = os.path.join(_existing_template_dir(), "appy", "director-movies.odt")
    dirname, name, path = p.split_template_name(abs_path)
    assert path == abs_path
    assert os.path.isabs(dirname)
    assert os.path.exists(path)


def test_subdir_nonexistent_returns_dirname_none():
    p = _FakePrintTool(_existing_template_dir())
    dirname, name, path = p.split_template_name("nope/missing.odt")
    assert dirname is None
    assert name == "missing.odt"


if __name__ == "__main__":
    run_tests(globals())
