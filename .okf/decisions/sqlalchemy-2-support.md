---
type: Decision
title: SQLAlchemy 2.x support
description: sqlkit 1.1.0 widened to dual SQLAlchemy 1.4 + 2.x support behind a compatibility shim.
tags: [sqlalchemy, migration, decision]
generated:
  by: process:okf-migrate
  at: 2026-11-24T00:00:00Z
sources:
  - resource: changelog
    title: '"1.1.0 - SQLAlchemy 2.x support - Jun 2026"'
  - resource: sqlkit/db/sacompat.py
  - resource: sqlkit/db/proxy.py
  - resource: pyproject.toml
---

# Context

The 1.0.0 port ran on the SQLAlchemy 1.4 baseline. Several APIs it relied on
were removed in SQLAlchemy 2.0 (classical `orm.mapper()`, implicit
`metadata.bind` execution, 1.x-style `select()` in FK filters).

# Decision (1.1.0)

Support **both 1.4 and 2.x** with a single codebase; the dependency pin is
`sqlalchemy>=1.4,<3` (`pyproject.toml`). Removed APIs are replaced with forms
that work on both, collected in `sqlkit/db/sacompat.py`:

* `sacompat.map_imperatively(...)` — wraps `registry().map_imperatively()`
  instead of classical `orm.mapper()` (`sqlkit/db/sacompat.py:38`).
* `autoload_with=` reflection and explicit connection execution.
* `metadata.bind` kept only as an informal engine-carrier; URL strings passed
  to [DbProxy](/components/dbproxy.md) are coerced to engines explicitly.

# Related driver work

psycopg 3 is supported as the `postgres` extra; `normalize_url()` routes plain
`postgresql://` URLs to `postgresql+psycopg://` when psycopg2 is absent
(`sqlkit/db/proxy.py:28`).

# Status

Achieved in the 1.1.x line (current repo version **1.2.0**). This supersedes
older notes that described SA2 support as "not started / use
`registry.map_imperatively` yourself" — the shim now does it.
