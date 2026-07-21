---
type: Megawidget
title: SqlTable
description: Multi-record editable grid — a view over a query with navigation, filtering and inline editing.
resource: sqlkit/widgets/table/table.py
tags: [core, widget, table]
timestamp: 2026-07-21T00:00:00Z
---

# Overview

`SqlTable` renders a query as an editable, multi-record grid. It shares its
constructor with the common base `SqlWidget`
(`sqlkit/widgets/common/sqlwidget.py:101`); `SqlTable` itself lives in
`sqlkit/widgets/table/table.py`. Clicking a column label opens the
[filter panel](/components/filtering.md); foreign-key cells get
[completion](/components/completion.md).

# Usage

```python
from sqlkit.widgets import SqlTable
from sqlkit.db import proxy

db = proxy.DbProxy(bind="sqlite:///movie.db")
t = SqlTable('movie', dbproxy=db, order_by='title', field_list='title year')
t.reload()          # run the query and populate the view
```

# Common constructor options

| Option        | Meaning                                                   | Demo |
|---------------|-----------------------------------------------------------|------|
| `what`        | table name (str) or a mapped class                        | `demo/sql/ex_01_table_movie.py` |
| `dbproxy=`    | the [DbProxy](/components/dbproxy.md)                      | all |
| `order_by=`   | Django-like: `'a b -c'` (`-` = DESC), `'rel__field'`      | `demo/sql/ex_13c_opts_order_by.py` |
| `field_list=` | whitelist of columns                                      | `demo/sql/ex_09_table_hide.py` |
| `hide_fields=`| blacklist of columns                                      | `demo/sql/ex_09_table_hide.py` |
| `rows=`       | visible rows                                              | `demo/sql/ex_13_opts_rows.py` |
| `format={}`   | per-field numeric/date formatting                         | `demo/sql/ex_13b_opts_format.py` |
| `geom=`       | `(w, h)` window geometry                                  | `demo/sql/ex_12_opts_geom.py` |
| `dev=True`    | show IDs even in read-only columns                        | `demo/sql/ex_10_opts_dev.py` |
| `hooks=`      | a [Hook](/components/hooks.md) instance                   | `demo/sql/ex_60_hooks_activate.py` |

# Mode (capabilities)

`mode` is a property of `Browse/Insert/Update/Delete` capability flags; set it
directly (`t.mode = 'b'`) or via `t.set_mode('biud')`
(`sqlkit/widgets/common/sqlwidget.py:890`). See `demo/sql/ex_08_table_noup.py`
and `demo/sql/ex_11_opts_mode.py`.

# Related concepts

Programmatic filters via [add_filter](/components/filtering.md); computed
columns and views via [custom fields](/components/custom-fields.md); GTK
[signals](/components/hooks.md) like `record-selected` for master/detail
composition (`demo/sql/ex_55_signals.py`).

# Citations

[1] `sqlkit/widgets/table/table.py`, `sqlkit/widgets/common/sqlwidget.py`.
[2] [doc/sqlkit/table.rst](../../doc/sqlkit/table.rst), [doc/sqlkit/browsing.rst](../../doc/sqlkit/browsing.rst)
