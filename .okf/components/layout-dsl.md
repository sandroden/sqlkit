---
type: DSL
title: Layout DSL
description: A concise mini-language that describes how fields and sub-widgets are arranged in a mask.
resource: sqlkit/layout
tags: [core, layout, mask]
timestamp: 2026-07-21T00:00:00Z
---

# Overview

The layout language is a multiline string that mixes **field names** and
**directives** to draw a [SqlMask](/components/sqlmask.md). It is parsed by the
`sqlkit/layout/` package (the layout generator wiring lives in
`sqlkit/widgets/common/layoutgenerator.py`). There is a standalone demo of the
language under `demo/layout/`.

# Grammar

| Token             | Meaning                                                | Demo |
|-------------------|--------------------------------------------------------|------|
| `field_name`      | editable field on the current model                    | `demo/sql/ex_02b_mask_movie.py` |
| `ro=field`        | read-only field                                        | `demo/sql/ex_02b_mask_movie.py` |
| `m2m=rel`         | many-to-many relation as an inline table               | `demo/sql/ex_25_relations_m2m.py` |
| `m2m=rel:f1,f2`   | m2m with a whitelist of columns                        | `demo/sql/ex_26_relations_m2m_table.py` |
| `o2m=rel`         | one-to-many (children)                                 | `demo/sql/ex_20_relations_movie.py` |
| `m2o=rel:f1,f2`   | many-to-one with inline fields                         | `demo/sql/ex_51_related_layout.py` |
| `{ ... }`         | box (vertical by default)                              | `demo/sql/ex_50_fancy_layout.py` |
| `{N.tabs ... }`   | notebook with `{ %tab_name ... }` sub-blocks           | `demo/sql/ex_50_fancy_layout.py` |
| `{.frame_id ... }`| frame with a CSS id, reachable as `m.widgets['f.frame_id']` | `demo/sql/ex_50_fancy_layout.py` |
| `%name`           | tab/section label                                      | `demo/sql/ex_50_fancy_layout.py` |
| `- - -`           | span across extra columns (context-dependent)          | `demo/sql/ex_25_relations_m2m.py` |
| newline           | new row (in a vertical box)                            | always |

# Pre-registering a layout

A layout can be cached module-wide so `SqlMask(model)` finds it automatically:

```python
from sqlkit.db import defaults
defaults.register_layout('movie', LAYOUT)     # sqlkit/db/defaults.py:232
# defaults.unregister_layout('movie')  to remove it
```

See `demo/sql/ex_66_hooks_on_init.py` for `register_layout` + `register_hook`
used together.

# Citations

[1] `sqlkit/layout/`, `sqlkit/widgets/common/layoutgenerator.py`, `sqlkit/db/defaults.py`.
[2] [doc/layout/layout.rst](../../doc/layout/layout.rst)
