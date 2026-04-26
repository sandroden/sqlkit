==========
 Printing
==========

Sqlkit can produce printable files (``.odt`` or ``.pdf``) from
OpenDocument templates. Two engines are bundled and the choice is made via
the module-level constant :attr:`sqlkit.misc.printing.PRINTING_STYLE`:

* **AppyPod** — default since the Py3 port. Wraps the third-party
  ``appy.pod`` library; templates are regular ``.odt``/``.ods`` files
  whose templating logic lives in document annotations
  (``do row for ... in ...``) and conditional-text fields. Producing an
  ``.odt`` output does not require a running OpenOffice/LibreOffice;
  rendering to ``.pdf`` is delegated to a separate Python interpreter
  with the ``uno`` module installed (see ``PY_PATH`` in
  :mod:`sqlkit.misc.appypod`, default ``/usr/bin/python3``).

* **Oootemplate** — legacy in-house engine kept for backward compatibility
  with installations that still depend on it. Powerful ``$obj.attr`` /
  ``++`` syntax but requires the ``uno`` module in the same Python that
  runs sqlkit, which is no longer available out-of-the-box on recent
  Ubuntu releases for Python 3.

In this module 'print' is used in a loose way: it always means producing
a printable file, never sending it to a physical printer.

.. note::

  Templates are looked up under ``self.template_dir`` (default:
  ``./templates``). The recommended layout splits them by engine in two
  sub-folders, ``templates/appy/`` and ``templates/oootemplate/``; this
  is just a convention — the engine is still picked by ``PRINTING_STYLE``
  (or by the per-widget ``printing_style`` argument), not by the path.

.. note::

  Generating ``.pdf`` requires a Python interpreter with the ``uno``
  module on ``PY_PATH``. On recent Ubuntu/Debian, ``uno`` is shipped
  with ``python3-uno`` and is normally available at
  ``/usr/bin/python3``. Generating ``.odt`` works without ``uno``.


.. automodule:: sqlkit.misc.printing




.. _psignals:

Signals
========


:context-ready:

   the context has been prepared. You can connect to this signal to add
   element to the context.

   .. function:: context_ready_cb(printtool, context, template_name, sqlwidget):
      
      :param printer: the printing.PrintTool object that emitted the signal
      :param context: the context 
      :param template_name: the template name that is rendered
      :param sqlwidget: the sqlwidget



.. _Openoffice.org: http://www.openoffice.org
.. _appy framework: http://appyframework.org/pod.html
