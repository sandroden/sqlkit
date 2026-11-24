---
okf_version: "0.2"
---

# sqlkit — knowledge bundle

**sqlkit** is a Python 3 / GTK 3 toolkit to edit the *data* of a database
(PostgreSQL, SQLite, MySQL, Firebird) on top of SQLAlchemy. Given a mapped
class or a table name it produces an editable grid ([SqlTable](/components/sqltable.md))
or a form ([SqlMask](/components/sqlmask.md)) with navigation, filtering,
completion, validation and relationship editing — with very little code.

This bundle captures the architecture, the extension points, the porting
decisions and the operational playbooks for **this repository** (version
1.2.0). Source of truth for every concept is a file that lives here:
`sqlkit/…`, `demo/sql/ex_*.py`, `doc/**/*.rst`, `changelog`.

# Components

* [DbProxy](/components/dbproxy.md) - connection/Session wrapper, entry point to every widget.
* [SqlTable](/components/sqltable.md) - multi-record editable grid megawidget.
* [SqlMask](/components/sqlmask.md) - single-record form megawidget (and MainSqlMask).
* [Layout DSL](/components/layout-dsl.md) - the mini-language that draws a mask.
* [Hooks](/components/hooks.md) - naming-convention callbacks, the main extension mechanism.
* [Relationships](/components/relationships.md) - editing o2m / m2m / m2o inline.
* [Completion](/components/completion.md) - autocompletion on plain and foreign-key fields.
* [Filtering](/components/filtering.md) - filter panel and Django-like programmatic filters.
* [Custom fields](/components/custom-fields.md) - computed columns and GUI field overrides.
* [Printing](/components/printing.md) - ODT/ODS templates via appy, context-ready signal.
* [sqledit](/components/sqledit.md) - the standalone, no-code GUI.

# Decisions

* [Python 3 / GTK 3 port](/decisions/py3-gtk3-port.md) - the porting from the Py2/GTK2 origin.
* [SQLAlchemy 2.x support](/decisions/sqlalchemy-2-support.md) - dual 1.4 + 2.x baseline.
* [GTK 4 evaluation](/decisions/gtk4-evaluation.md) - not started; risks and reference.

# Playbooks

* [Dev setup](/playbooks/dev-setup.md) - uv venv with system PyGObject.
* [Running demos](/playbooks/running-demos.md) - demos as the primary test surface.
* [Known pitfalls](/playbooks/known-pitfalls.md) - the trap catalog for this port.
