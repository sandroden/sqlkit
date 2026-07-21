---
type: Feature
title: Relationships
description: Editing one-to-many, many-to-many and many-to-one relations inline in a mask.
resource: doc/sqlkit/relationship.rst
tags: [relations, mask, editing]
timestamp: 2026-07-21T00:00:00Z
---

# Overview

A [SqlMask](/components/sqlmask.md) can embed related records as inline tables,
declared in the [layout DSL](/components/layout-dsl.md) with `o2m=`, `m2m=` and
`m2o=`. Runtime handles hang off `mask.related.<rel>`.

# One-to-many (children)

```python
LAYOUT = "first_name last_name o2m=movies - - -"
m = SqlMask('director', dbproxy=db, layout=LAYOUT)
m.related.movies.modelproxy.order_by('year')
```

Demos: `demo/sql/ex_20_relations_movie.py`, `demo/sql/ex_21_relations_select_fields.py`.

# Many-to-many

```python
LAYOUT = "title year m2m=genres - m2m=actors -"
m = SqlMask('movie', dbproxy=db, layout=LAYOUT)
m.related.actors.set_editable(True)     # allow add/remove
```

Demos: `demo/sql/ex_25_relations_m2m.py`, `demo/sql/ex_26_relations_m2m_table.py`,
`demo/sql/ex_27_relations_m2m_editable.py`.

# Filtering across a relation (join)

Django-like double-underscore joins, applied via [add_filter](/components/filtering.md):

```python
m.add_filter(movies__title__icontains='il')
m.add_filter(movies__year__gte=2000)
```

Demos: `demo/sql/ex_22_relations_filter_join.py`, `demo/sql/ex_23_relations_filter_join.py`.

# Completion inside relations

Foreign-key columns of an embedded table get [completion](/components/completion.md);
`demo/sql/ex_40d_completion_m2m_fkey.py` and `ex_40e_...` cover m2m FK completion.

# Citations

[1] [doc/sqlkit/relationship.rst](../../doc/sqlkit/relationship.rst)
[2] Demos `demo/sql/ex_20*`–`ex_27*`.
