---
type: Megawidget
title: SqlMask
description: Single-record form megawidget driven by a layout string; can embed related tables.
resource: sqlkit/widgets/mask/mask.py
tags: [core, widget, mask]
timestamp: 2026-07-21T00:00:00Z
---

# Overview

`SqlMask` renders one record at a time as a form, with navigation buttons and
a filter panel. Its shape is described by a [layout DSL](/components/layout-dsl.md)
string, which is the main difference from [SqlTable](/components/sqltable.md).
A mask can embed [related records](/components/relationships.md) as inline
tables. Defined in `sqlkit/widgets/mask/mask.py`; constructor shared with
`SqlWidget` (`sqlkit/widgets/common/sqlwidget.py:101`).

`MainSqlMask` is the same widget wrapped in a `Gtk.Window` with a ready-made
menu/toolbar (see `demo/sql/ex_70_uimanager_custom.py`).

# Usage

```python
from sqlkit.widgets import SqlMask
from sqlkit.db import proxy

db = proxy.DbProxy(bind="sqlite:///movie.db")

LAYOUT = """
title
year director_id
ro=id
"""
m = SqlMask('movie', dbproxy=db, layout=LAYOUT, order_by='title')
m.reload()
```

# Notable options

* `layout=` — the [layout DSL](/components/layout-dsl.md) string (or omit to
  reuse one pre-registered via `register_layout`).
* `single=True` — pop up an editor for a single record.
* `hooks=` — a [Hook](/components/hooks.md) instance.
* `flip_buttons=True` — reverse the direction of the navigation arrows
  (added in 1.1.1, see `changelog`).

# Runtime handles

```python
m.current                 # the current mapped object
m.session                 # the SQLAlchemy Session
m.set_value('field', v)   # set a widget value
m.widgets['f.<id>']       # a layout container declared with {.id ...}
m.related.<rel>           # an embedded relationship view
m.completions.<fk>        # a completion controller
m.defaults.fk(...)        # a foreign-key default
```

# Citations

[1] `sqlkit/widgets/mask/mask.py`, `sqlkit/widgets/common/sqlwidget.py`.
[2] [doc/sqlkit/mask.rst](../../doc/sqlkit/mask.rst)
[3] Demos: `demo/sql/ex_02b_mask_movie.py`, `demo/sql/ex_50_fancy_layout.py`, `demo/sql/ex_70_uimanager_custom.py`.
