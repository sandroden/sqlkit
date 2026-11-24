---
type: Feature
title: Custom fields & computed columns
description: Subclass Field to add computed columns, and override the GUI field type per column.
resource: sqlkit/fields.py
tags: [fields, columns, customization]
generated:
  by: process:okf-migrate
  at: 2026-11-24T00:00:00Z
sources:
  - resource: sqlkit/fields.py
  - resource: sqlkit/widgets/table/columns.py
  - resource: sqlkit/widgets/table/cell_renderers.py
  - resource: "demo/sql/ex_30_mapper_count.py–ex_35_custom__obj__.py"
    title: "Demos"
---

# Overview

The field layer (`sqlkit/fields.py`) maps DB/SA types to GUI widgets. You
extend it to add computed columns or to override how a column is rendered and
cleaned. `VarcharField` (`sqlkit/fields.py:795`) is the usual base for a
text-derived computed column.

# A computed column

```python
from sqlkit import fields

class ObjField(fields.VarcharField):
    @fields.std_cleanup
    def clean_value(self, value):
        return "%(year)s %(title)s" % value

# add it to a table view
t.views['main'].add_column(field=ObjField('label', {...}), position=0)
```

`std_cleanup` is a decorator on `Field` (`sqlkit/fields.py:766`) that wraps a
plain `clean_value`. Demos: `demo/sql/ex_31_add_field.py`,
`demo/sql/ex_32_count_movies.py`, `demo/sql/ex_35_custom__obj__.py`.

# Column width

The initial width of a text-like column (`VarcharColumn` and subclasses in
`sqlkit/widgets/table/columns.py`) is decided in advance by
`CellRendererVarchar` (`sqlkit/widgets/table/cell_renderers.py`), not by the
content: `col_width=` (in average chars), else the DB length, clamped to the
column's `MIN_DEFAULT_WIDTH`/`MAX_DEFAULT_WIDTH`. Dates, datetimes and times
are measured instead on formatted samples (`width_samples()`, every month and
weekday in the field's format), numbers on `get_width()` digits. A custom
column can override `width_samples()` / `width_samples_key()`. See pitfall 5
in [known pitfalls](/playbooks/known-pitfalls.md) for why this lives in
`do_get_preferred_width`.

# GUI field mapping

Override the GUI field class of a column before the widgets are built, from an
[on_pre_layout hook](/components/hooks.md) or the `gui_field_mapping=`
constructor argument (`sqlkit/widgets/common/sqlwidget.py`):

```python
def on_pre_layout(self, widget):
    widget.gui_field_mapping = {'costo': CostoField}
```
