---
type: Decision
title: Python 3 / GTK 3 port
description: sqlkit was ported from its Python 2 / PyGTK 2 origin to Python 3 and GTK 3 (PyGObject).
tags: [porting, gtk3, python3, decision]
timestamp: 2026-07-21T00:00:00Z
---

# Context

sqlkit originated as a Python 2 / PyGTK 2 library (last legacy release
`0.9.6.1`, Mar 2014 — see `changelog`). This repository is the Python 3 / GTK 3
(PyGObject) port, released as **1.0.0** (Jun 2026).

# Decision

* Target Python `>=3.10` and GTK 3 via PyGObject.
* PyGObject is consumed from the **system** (apt `python3-gi`, `gir1.2-gtk-3.0`),
  not from PyPI — see [dev setup](/playbooks/dev-setup.md).
* `gi.require_version('Gtk', '3.0')` is pinned in `sqlkit/__init__.py` before
  any GTK import, so the resolver cannot latch onto GTK 4.

# Consequences worth remembering

* GTK2-era `modify_base` / `modify_text` colouring was silently ignored by GTK3
  CSS themes; highlighting (NOT NULL yellow background, navy FK labels, DateEdit
  flash) was reimplemented with `Gtk.CssProvider` in 1.1.0.
* Legacy `gobject.idle_add(...)` becomes `GLib.idle_add(...)` from
  `gi.repository`. See [known pitfalls](/playbooks/known-pitfalls.md).

The 1.0.0 changelog entry lists the port fixes (join modes in DbProxy,
InspectMapper with relationships, csv export, calendar popup, completion).

# Citations

[1] `changelog` — entries "1.0.0 - GTK3 / Python 3 port" and "1.1.0".
[2] `sqlkit/__init__.py`, `README`.
[3] Related: [SQLAlchemy 2.x support](/decisions/sqlalchemy-2-support.md), [GTK 4 evaluation](/decisions/gtk4-evaluation.md).
