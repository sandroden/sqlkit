---
type: Application
title: sqledit
description: The standalone, no-code GUI — point it at a database URL and start editing.
resource: sqlkit/scripts/sqledit.py
tags: [cli, gui, standalone]
generated:
  by: process:okf-migrate
  at: 2026-07-21T00:00:00Z
sources:
  - resource: sqlkit/scripts/sqledit.py
  - resource: pyproject.toml
  - resource: "../../doc/misc/sqledit.rst"
    title: "doc/misc/sqledit.rst"
---

# Overview

`sqledit` is a ready-made GUI that needs no programming: give it a database URL
and it lets you browse and edit tables using the same
[SqlTable](/components/sqltable.md) / [SqlMask](/components/sqlmask.md) widgets.
It is exposed as a GUI entry point (`pyproject.toml`,
`[project.gui-scripts] sqledit = "sqlkit.scripts.sqledit:main"`); `main()` is at
`sqlkit/scripts/sqledit.py:394`.

# Usage

```
sqledit sqlite:///movie.db
sqledit postgresql://user:pwd@host/db
```

`demo/sql/ex_99_sqledit.py` drives it programmatically.
