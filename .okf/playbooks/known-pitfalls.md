---
type: Playbook
title: Known pitfalls
description: Traps specific to the Py3/GTK3 port and to sqlkit's programming model.
tags: [pitfalls, gtk3, sqlalchemy, gotchas]
timestamp: 2026-07-21T00:00:00Z
---

# GTK / PyGObject

1. **`gi.require_version` first.** Call `gi.require_version('Gtk', '3.0')`
   before importing GTK, or the resolver may pick GTK 4. The package does this
   in `sqlkit/__init__.py`; app code that imports GTK directly must too.

2. **Venv needs `--system-site-packages`.** PyGObject comes from the system;
   pip-installing it into the venv usually fails or conflicts. See
   [dev setup](/playbooks/dev-setup.md).

3. **`gobject.idle_add` is legacy.** Py2/GTK2 code uses `gobject.idle_add(...)`;
   in Py3/GTK3 use `from gi.repository import GLib; GLib.idle_add(...)`.

4. **Defaults on a m2m collection in `on_init`.** Setting a collection value
   right away can race with layout rendering; defer it with `GLib.idle_add`.

# SQLAlchemy

5. **Classical `mapper()` is gone in SA 2.x.** Use
   `sqlkit.db.sacompat.map_imperatively(...)` (works on 1.4 and 2.x). See
   [SQLAlchemy 2.x support](/decisions/sqlalchemy-2-support.md).

# Programming model

6. **No side-effects in validation.** Do not send email / touch the outside
   world in `on_field_validation` or `on_pre_save` — the flush can fail and
   leave a phantom effect. Record the intent and act in `on_after_commit`. See
   [hooks](/components/hooks.md).

7. **i18n label vs DB column name collision.** The translation layer can rewrite
   a field name that collides with an i18n label; use a display alias different
   from the real DB column when it happens.

# Citations

[1] `sqlkit/__init__.py`, `sqlkit/db/sacompat.py`.
[2] Related: [hooks](/components/hooks.md), [SQLAlchemy 2.x support](/decisions/sqlalchemy-2-support.md), [dev setup](/playbooks/dev-setup.md).
