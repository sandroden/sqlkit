---
type: Component
title: DbProxy
description: Wrapper over the SQLAlchemy engine/metadata/Session, passed to every sqlkit widget.
resource: sqlkit/db/proxy.py
tags: [core, database, sqlalchemy]
timestamp: 2026-07-21T00:00:00Z
---

# Overview

`DbProxy` is the single entry point that binds sqlkit to a database. You build
it once and pass it as `dbproxy=` to [SqlTable](/components/sqltable.md),
[SqlMask](/components/sqlmask.md) and every other widget. It owns the engine,
the reflected `MetaData`, and hands out SQLAlchemy `Session`s.

Defined in `sqlkit/db/proxy.py` (`class DbProxy`, `__init__` at line 72).

# Usage

```python
from sqlkit.db import proxy

db = proxy.DbProxy(bind="postgresql://user:pwd@host/db")
db = proxy.DbProxy(bind="sqlite:///file.db")
db = proxy.DbProxy(engine=existing_engine)   # reuse an engine you already have
```

`__init__` accepts `metadata=`, `engine=`, `bind=` (a URL string or engine)
among others. URL strings are coerced to engines explicitly — see the SA 2.x
notes in [SQLAlchemy 2.x support](/decisions/sqlalchemy-2-support.md).

# PostgreSQL driver routing

`normalize_url()` (`sqlkit/db/proxy.py:28`) rewrites a plain `postgresql://`
URL to the psycopg 3 driver (`postgresql+psycopg://`) when psycopg2 is not
installed. Install the driver with the `postgres` extra:

```
uv sync --extra postgres      # or: pip install sqlkit[postgres]
```

# Citations

[1] `sqlkit/db/proxy.py` — `DbProxy`, `normalize_url`.
[2] [Dev setup playbook](/playbooks/dev-setup.md)
