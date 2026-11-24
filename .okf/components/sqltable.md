---
type: Megawidget
title: SqlTable
description: Multi-record editable grid — a view over a query with navigation, filtering and inline editing.
resource: sqlkit/widgets/table/table.py
tags: [core, widget, table]
timestamp: 2026-11-24T00:00:00Z
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

# Totals

`t.totals` (`sqlkit/widgets/table/totals.py`) sums numeric columns
(`add_total`) with optional subtotals on break fields (`add_break`,
`add_date_break`); also available from the column menu. Totals are extra
`TotalObj` rows inserted in the model; the `computed` signal carries the
grand totals. Since 2026-11 the grand totals are also shown in a fixed strip
under the table (`TotalsFooter`, `sqlkit/widgets/table/totals_footer.py`),
visible without scrolling: it mirrors width, visibility and order of the main
columns and follows the horizontal scroll; columns with a total get a
`min-width` large enough not to clip it. While the grand total row is fully
visible (short tables, inlines, scrolled to the bottom) the strip is made
transparent (opacity, not hidden, to avoid a layout jump). `Totals.footer =
False` disables it;
`hide_total=True` hides it. Only the main treeview gets a footer (not the
filter panel output). Demo: `demo/sql/ex_03_table_totals.py`.

# Related concepts

Programmatic filters via [add_filter](/components/filtering.md); computed
columns and views via [custom fields](/components/custom-fields.md); GTK
[signals](/components/hooks.md) like `record-selected` for master/detail
composition (`demo/sql/ex_55_signals.py`).

# Citations

[1] `sqlkit/widgets/table/table.py`, `sqlkit/widgets/common/sqlwidget.py`.
[2] [doc/sqlkit/table.rst](../../doc/sqlkit/table.rst), [doc/sqlkit/browsing.rst](../../doc/sqlkit/browsing.rst)
