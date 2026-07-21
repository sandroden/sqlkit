# Components

The core widgets and features of sqlkit. Each concept cites the source file,
the `doc/**/*.rst` chapter, and runnable `demo/sql/ex_*.py` snippets in this
repository.

# Core

* [DbProxy](dbproxy.md) - connection/Session wrapper, entry point to every widget.
* [SqlTable](sqltable.md) - multi-record editable grid megawidget.
* [SqlMask](sqlmask.md) - single-record form megawidget (and MainSqlMask).
* [Layout DSL](layout-dsl.md) - the mini-language that draws a mask.
* [Hooks](hooks.md) - naming-convention callbacks, the main extension mechanism.

# Features

* [Relationships](relationships.md) - editing o2m / m2m / m2o inline.
* [Completion](completion.md) - autocompletion on plain and foreign-key fields.
* [Filtering](filtering.md) - filter panel and Django-like programmatic filters.
* [Custom fields](custom-fields.md) - computed columns and GUI field overrides.
* [Printing](printing.md) - ODT/ODS templates via appy.

# Applications

* [sqledit](sqledit.md) - the standalone, no-code GUI.
