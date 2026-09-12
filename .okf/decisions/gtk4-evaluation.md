---
type: Decision
title: GTK 4 evaluation
description: A future GTK 4 migration was evaluated but not started; the key risk is in-cell editing.
tags: [gtk4, migration, evaluation, decision]
generated:
  by: process:okf-migrate
  at: 2026-07-21T00:00:00Z
sources:
  - resource: "Internal GTK 4 migration evaluation (deep-research, 2026)"
  - resource: "/decisions/py3-gtk3-port.md"
    title: "Python 3 / GTK 3 port"
---

# Status

**Not started.** A migration from GTK 3 to GTK 4 was investigated (deep-research,
mid-2026) as a possible future direction. No code work has begun.

# Key finding

The dominant risk is **in-cell editing** in the tabular view
([SqlTable](/components/sqltable.md)): GTK 4 dropped the classic
`Gtk.TreeView` / `CellRenderer` editing model that sqlkit's grid relies on
(`sqlkit/widgets/table/cell_renderers.py`, `columns.py`), and there is no
drop-in native replacement. The suggested reference direction is a
`gtk4-db-binder` style approach built on `Gtk.ColumnView`.

# Decision

Stay on GTK 3 for now. Revisit only if GTK 3 / PyGObject support becomes a
blocker; treat in-cell editing as the make-or-break spike before committing.
