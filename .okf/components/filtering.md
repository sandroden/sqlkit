---
type: Feature
title: Filtering
description: Interactive filter panel and Django-like programmatic filters with relative dates and joins.
resource: sqlkit/widgets/common/sqlfilter.py
tags: [filter, query, search]
timestamp: 2026-07-21T00:00:00Z
---

# Overview

Every field can filter the visible records. Interactively, clicking a column
label / field label opens the **filter panel**; programmatically, `add_filter`
accepts Django-like keyword conditions. The implementation lives in
`sqlkit/widgets/common/sqlfilter.py` (`add_filter` at line 361).

# Programmatic filters

```python
t.add_filter(title__icontains='il')
t.add_filter(year__gte=2000, year__lt=2010)
t.add_filter(director__nation='IT')      # implicit join across a relation
t.reload()                               # apply and re-query
```

Operators: `__icontains`, `__gt`, `__gte`, `__lt`, `__lte`, `__null`,
`__regexp`, and relative-date forms such as `__@m-1` (last month — see
`demo/sql/ex_07_date_relative.py`).

Demos: `demo/sql/ex_04_table_filter.py`, `demo/sql/ex_06_table_filter.py`,
`demo/sql/ex_36_filter_panel_tree.py`.

# Injecting records without SQL

`set_records` replaces the visible rows with an arbitrary list (e.g. aggregated
rows) bypassing the query — `sqlkit/widgets/mask/mask.py:742`:

```python
m.set_records([])                # clear
m.set_records(custom_rows)       # inject
```

# Backend-specific translation

The filter panel translates operators per backend: `icontains` maps to
`regexp` on PostgreSQL/MySQL (see `changelog` and recent git history). Boolean
columns coerce string booleans in Django-style filters.

# Citations

[1] `sqlkit/widgets/common/sqlfilter.py`, `sqlkit/db/django_syntax.py`.
[2] [doc/sqlkit/filters.rst](../../doc/sqlkit/filters.rst)
