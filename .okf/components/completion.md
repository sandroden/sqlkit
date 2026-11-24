---
type: Feature
title: Completion
description: Autocompletion on plain and foreign-key fields, with runtime filtering and cascades.
resource: sqlkit/widgets/common/completion.py
tags: [completion, foreign-key, ux]
generated:
  by: process:okf-migrate
  at: 2026-07-21T00:00:00Z
sources:
  - resource: sqlkit/widgets/common/completion.py
  - resource: "../../doc/sqlkit/completion.rst"
    title: "doc/sqlkit/completion.rst"
  - resource: "demo/sql/ex_40*–ex_43*"
    title: "Demos"
---

# Overview

Every field, and in particular every foreign-key field, gets autocompletion.
The controller is reachable at `widget.completions.<field>`; the machinery
lives in `sqlkit/widgets/common/completion.py`.

# Usage

```python
m.completions.director_id.filter(nation='IT')
m.completions.director_id.format = '%(last_name)s %(first_name)s'
```

# Dynamic completion (depends on another field)

Reference another field's value with `$`:

```python
m.completions.job_id.filter(client_id='$client_id')
```

Demo: `demo/sql/ex_42_completion_dinamic.py`.

# Cascade via on_completion hook

When a completion row is selected, an [on_completion hook](/components/hooks.md)
can populate other fields:

```python
class JoinHook:
    def on_completion__job_id(self, m, fname, obj):
        m.set_value('numero_job', obj['numero_job'])
```

Demo: `demo/sql/ex_62_hooks_completion.py`.

# Autostart / group-by

Autostart completion after N chars: `demo/sql/ex_41_completion_autostart.py`
(and `ex_41b`, `ex_41c`). Group-by output: `demo/sql/ex_43_completion_group_by.py`.
