"""End-to-end render of the demo AppyPod template.

This is the runtime test that ex_77 implicitly exercises through the GUI
(File → Print). Driving it from Python lets us exercise the printing
pipeline in CI without a Gtk main loop.

What this test covers:

* the AppyPod template ``demo/sql/templates/appy/director-movies.odt``
  parses cleanly under the appy.pod version pinned in the venv (the Py2
  template originally used ``condition="ooow:1"`` which modern appy.pod
  rejects with ``ParsingError: Wrong meta-condition "1"`` — the
  template was patched to ``ooow:'1'``);
* ``AppyPodTemplate(...).render('odt')`` returns a non-empty ZIP-magic
  bytes blob (the ODT container) — i.e. all three Py3 traps that ex_77
  hit (``rwb`` mode, text-mode ``save_as``, the meta-condition syntax)
  stay fixed;
* the rendered ODT contains values from the SQLAlchemy objects passed
  in the context, proving that the ``do row for f in obj.movies``
  iteration and the ``f.title``/``f.year`` cell expressions both work.

We deliberately do NOT exercise PDF rendering: that requires LibreOffice
+ a Python with ``uno`` bindings on ``PY_PATH``, which is an environment
concern outside the scope of the porting trap suite.
"""
import os
import re
import unittest
import zipfile

from _harness import ensure_path, run_tests
ensure_path()


def _require_appy():
    try:
        import appy.pod  # noqa: F401
    except ImportError:
        raise unittest.SkipTest("appy not installed (optional extra: sqlkit[printing])")


def _build_director_with_movies():
    """In-memory SQLite + tiny Director/Movie schema with one populated row."""
    from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
    from sqlalchemy.orm import declarative_base, relationship, sessionmaker

    Base = declarative_base()

    class Director(Base):
        __tablename__ = "director"
        id = Column(Integer, primary_key=True)
        first_name = Column(String(60), nullable=False)
        last_name = Column(String(60), nullable=False)
        nation = Column(String(6))
        movies = relationship("Movie", back_populates="director",
                              cascade="all, delete-orphan")

    class Movie(Base):
        __tablename__ = "movie"
        id = Column(Integer, primary_key=True)
        title = Column(String(60), nullable=False)
        description = Column(String(512))
        year = Column(Integer)
        director_id = Column(Integer, ForeignKey("director.id"), nullable=False)
        director = relationship("Director", back_populates="movies")

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    # expire_on_commit=False: keep loaded attributes accessible after
    # commit so appy.pod's eval(`obj.movies`) doesn't trip a lazy load
    # on a detached instance.
    s = sessionmaker(bind=engine, expire_on_commit=False)()
    d = Director(first_name="Akira", last_name="Kurosawa", nation="JP")
    d.movies.extend([
        Movie(title="Ran", year=1985, description="King Lear with samurai"),
        Movie(title="Rashomon", year=1950, description="Same crime, four stories"),
    ])
    s.add(d)
    s.commit()
    return d


def _template_path():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.normpath(os.path.join(here, "..", ".."))
    return os.path.join(root, "demo", "sql", "templates", "appy", "director-movies.odt")


def test_appy_template_renders_odt():
    _require_appy()
    from sqlkit.misc.appypod import AppyPodTemplate

    director = _build_director_with_movies()
    template = _template_path()
    assert os.path.exists(template), template

    data = AppyPodTemplate(template, {"obj": director}).render(file_type="odt")

    assert isinstance(data, (bytes, bytearray)), type(data)
    assert len(data) > 1024, "rendered ODT looks suspiciously small: %d bytes" % len(data)
    # ODT files are ZIP containers — first 4 bytes are the local file header.
    assert data[:4] == b"PK\x03\x04", "missing ZIP magic; got %r" % data[:4]


def test_appy_template_includes_iteration_values():
    """The 'do row for f in obj.movies' loop must inject Movie attributes
    into the rendered content.xml."""
    _require_appy()
    from sqlkit.misc.appypod import AppyPodTemplate
    import io

    director = _build_director_with_movies()
    data = AppyPodTemplate(_template_path(), {"obj": director}).render(file_type="odt")

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        content = zf.read("content.xml").decode("utf-8")

    # The director header fields and the movie loop fields all flow from
    # the SA objects through appy's expression evaluator into content.xml.
    for needle in ("Akira", "Kurosawa", "Ran", "Rashomon", "1985", "1950"):
        assert needle in content, \
            "%r not found in rendered content.xml (loop/header expression broken?)" % needle


def test_appy_template_no_legacy_meta_condition():
    """Guard the in-place fix of the template: the Py2 meta-condition
    `ooow:1` (bare integer) is rejected by modern appy.pod with
    ParsingError; it was rewritten to `ooow:'1'` (string-quoted)."""
    with zipfile.ZipFile(_template_path()) as zf:
        content = zf.read("content.xml").decode("utf-8")
    assert "ooow:1" not in content, \
        "template still contains legacy meta-condition `ooow:1`; expected `ooow:'1'`"
    # Sanity: the patched form must be present (else the iteration
    # expressions silently became inert).
    assert re.search(r"ooow:['\"]1['\"]", content), \
        "patched meta-condition `ooow:'1'` missing from template"


if __name__ == "__main__":
    run_tests(globals())
