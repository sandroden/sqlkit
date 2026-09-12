---
type: Feature
title: Custom fields & computed columns
description: Subclass Field to add computed columns, and override the GUI field type per column.
resource: sqlkit/fields.py
tags: [fields, columns, customization]
generated:
  by: process:okf-migrate
  at: 2026-07-21T00:00:00Z
sources:
  - resource: sqlkit/fields.py
  - resource: sqlkit/widgets/table/columns.py
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

# GUI field mapping

Override the GUI field class of a column before the widgets are built, from an
[on_pre_layout hook](/components/hooks.md) or the `gui_field_mapping=`
constructor argument (`sqlkit/widgets/common/sqlwidget.py`):

```python
def on_pre_layout(self, widget):
    widget.gui_field_mapping = {'costo': CostoField}
```
