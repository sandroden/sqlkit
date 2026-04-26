============
Printing
============

Sqlkit produces printable files (``.odt`` or ``.pdf``) from
OpenDocument templates via two pluggable engines:

* **AppyPod** (default) — uses the third-party ``appy.pod`` library;
  templates carry their logic in document annotations and conditional
  text. Rendering to ``.odt`` does not need a running
  OpenOffice/LibreOffice; ``.pdf`` rendering is delegated to a separate
  Python interpreter with the ``uno`` module.

* **Oootemplate** (legacy) — in-house engine with ``$obj.attr`` and
  ``++`` row-iteration syntax. Requires the ``uno`` module in the same
  Python that runs sqlkit and is kept only for backward compatibility.

Per-engine API and template-syntax details are documented inline in the
module docstring (see :mod:`sqlkit.misc.printing`); for end-to-end
examples see ``demo/sql/ex_75_printing.py`` … ``ex_79_printing-related-fk.py``
and the templates under ``demo/sql/templates/{appy,oootemplate}/``.

.. automodule:: sqlkit.misc.printing
