---
type: Extension Mechanism
title: Hooks
description: Naming-convention callbacks invoked by the framework on mask/table events — the main way to customize behaviour.
resource: sqlkit/db/defaults.py
tags: [core, extension, validation]
timestamp: 2026-07-21T00:00:00Z
---

# Overview

A *hook* is a plain Python object whose methods follow a naming convention;
the framework calls them by name on widget events. You pass an instance as
`hooks=` to a [SqlMask](/components/sqlmask.md) / [SqlTable](/components/sqltable.md),
or register a class globally per table with
`sqlkit.db.defaults.register_hook` (`sqlkit/db/defaults.py:162`).

# Hook catalogue

| Hook                                            | When                              | Demo |
|-------------------------------------------------|-----------------------------------|------|
| `on_init(mask)`                                 | mask built, before first reload   | `demo/sql/ex_66_hooks_on_init.py` |
| `on_activate__<f>(m, fname, fld)`               | Enter on a field                  | `demo/sql/ex_60_hooks_activate.py` |
| `on_field_validation__<f>(m, fname, val, fld)`  | per-field; raise `ValidationError`| `demo/sql/ex_63_hooks_field_validation.py` |
| `on_change_value__<f>(m, fname, val, fld)`      | value changed                     | `demo/sql/ex_63c_change_value.py` |
| `on_completion__<f>(m, fname, obj)`             | a completion (FK) row selected    | `demo/sql/ex_62_hooks_completion.py` |
| `on_pre_save(m, obj, session)`                  | before flush; raise to block      | `demo/sql/ex_64_hooks_validate.py` |
| `on_after_flush(m, obj, session)`               | after flush, before commit        | `demo/sql/ex_65_hooks-after-flush.py` |
| `on_after_commit(m, obj, session)`              | after commit — transaction-safe   | `demo/sql/ex_67_register_and_commit.py` |

# Registration

```python
from sqlkit.db import defaults
defaults.register_hook('movie', MovieHooks)          # sqlkit/db/defaults.py:162
# or, re-exported:
from sqlkit.db import register_hook
register_hook('movie', MovieHooks)
```

`nick=` lets two different hooks bind to the same table for different views.

# Side-effects must be rollback-safe

Do **not** send email / mutate the outside world from `on_field_validation` or
`on_pre_save`: the flush can still fail and leave a phantom effect. Record the
intent in the hook, execute it only in `on_after_commit`. See
[known pitfalls](/playbooks/known-pitfalls.md).

# GTK signals (alternative)

For master/detail composition of two independent widgets, connect to GTK
signals instead of embedding: `record-selected`, `record-saved`, `after-flush`
(`demo/sql/ex_55_signals.py`, `demo/sql/ex_56_signals-after-flush.py`).

# Citations

[1] `sqlkit/db/defaults.py`, `sqlkit/db/__init__.py` (re-exports).
[2] [doc/sqlkit/validation.rst](../../doc/sqlkit/validation.rst)
