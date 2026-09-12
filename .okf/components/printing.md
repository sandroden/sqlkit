---
type: Feature
title: Printing
description: Generate ODT/ODS documents from templates via appy, filling context on the context-ready signal.
resource: doc/printing/contents.rst
tags: [printing, odt, reporting, optional]
generated:
  by: process:okf-migrate
  at: 2026-07-21T00:00:00Z
sources:
  - resource: "../../doc/printing/contents.rst"
    title: "doc/printing/contents.rst"
  - resource: "demo/sql/ex_75_printing.py–ex_79_printing-related-fk.py"
    title: "Demos"
---

# Overview

sqlkit can print the current record (and its relations) through ODT/ODS
templates. The engine is `appy.pod`, shipped as the **optional** `printing`
extra. Templates live under `demo/sql/templates/` in the demos.

```
uv sync --extra printing        # or: pip install sqlkit[printing]
```

If `appy` is absent the printing tests skip rather than fail (see
[running demos](/playbooks/running-demos.md)).

# Wiring a menu entry and filling context

```python
def setup_printing(self, m):
    m.printing.add_menu_entry('Report (pdf)', 'report.odt')
    m.printing.connect('context-ready', self.prepare_context)

def prepare_context(self, printtool, context, template_name, sqlwidget):
    if template_name == 'report.odt':
        context.update({'total': sum(r.importo for r in sqlwidget.current.rows)})
```

# Demos

`demo/sql/ex_75_printing.py`, `ex_76_printing_translate.py`,
`ex_77_printing-related.py`, `ex_78_printing-fk.py`,
`ex_79_printing-related-fk.py`.
