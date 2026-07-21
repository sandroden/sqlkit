---
type: Playbook
title: Dev setup
description: Create the uv venv with system PyGObject and install dependencies.
tags: [setup, uv, pygobject, gtk3]
timestamp: 2026-07-21T00:00:00Z
---

# Why this is special

PyGObject / GTK 3 are consumed from the **system**, not from PyPI. Building
PyGObject from source needs `libgirepository-2.0-dev` (present on Ubuntu 24.04
but not installed by default). So the venv must see system site-packages.

# Steps

```bash
# system packages (Ubuntu/Debian)
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gtksource-3.0

# venv that can see system PyGObject
uv venv --system-site-packages
uv sync                       # installs SQLAlchemy, Babel, python-dateutil + dev group

# optional extras
uv sync --extra printing      # appy (ODT/ODS printing)
uv sync --extra postgres      # psycopg 3 driver
```

Run anything inside the venv with `uv run`:

```bash
uv run python -c "import sqlkit; print(sqlkit.__version__)"
```

# Notes

* Requires-python is `>=3.10` (`pyproject.toml`).
* The `dev` dependency group (`sphinx`, `pytest`, `pydata-sphinx-theme`) is
  installed by `uv sync` by default (PEP 735).
* See [running demos](/playbooks/running-demos.md) for the GUI display setup.

# Citations

[1] `README`, `pyproject.toml`, `CLAUDE.md`.
[2] Related: [DbProxy](/components/dbproxy.md), [Python 3 / GTK 3 port](/decisions/py3-gtk3-port.md).
