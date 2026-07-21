---
type: Playbook
title: Running demos & tests
description: The demos are the primary test surface; how to run them headless and run the pytest suites.
tags: [demo, test, pytest, gtk3]
timestamp: 2026-07-21T00:00:00Z
---

# Demos as the primary test surface

The 90+ runnable snippets under `demo/sql/ex_*.py` are the best way to exercise
a feature end-to-end. Each is self-contained and does not require installation:

```bash
uv run python demo/sql/ex_01_table_movie.py
```

For GUI runs on a headless / Wayland box, force X11 + Xvfb:

```bash
env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a uv run python demo/sql/ex_02b_mask_movie.py
```

`demo/sql/demo.py` and `demo/demo_tour.py` provide a browsable index of the
snippets.

# Test suites

```bash
uv run pytest                                   # main suite (testpaths=test)
```

`pytest.ini` marks GTK tests with `gtk` (run under `xvfb-run -a`) and excludes
two legacy harnesses that keep their own runners:

```bash
uv run python test/regress_porting_traps/run_all.py     # porting-trap regressions
```

`appy` is optional: without it the printing regressions skip rather than fail.

# Citations

[1] `pytest.ini`, `README`, `CLAUDE.md`.
[2] `changelog` — "new pytest suite (177 tests, sqlite in-memory by default)".
[3] Related: [dev setup](/playbooks/dev-setup.md).
