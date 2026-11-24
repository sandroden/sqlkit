SQLKIT — porting Py3/Gtk3
=========================

Questo repo (`sqlkit-gtk3/`) è il target del porting Py3/Gtk3 di sqlkit.
Lo sviluppo avviene in Mercurial con i topic (`hg topic <name>`); commit
piccoli e tematici, mai accumulati.

Comandi canonici (uv)
---------------------

L'ambiente è gestito con `uv` e usa il PyGObject di sistema (Ubuntu
24.04: `python3-gi`, `gir1.2-gtk-3.0`) tramite venv con
`--system-site-packages`.

Setup iniziale del venv:

    uv venv --system-site-packages
    uv sync

Esecuzione di script / moduli nel venv:

    uv run python -c "import sqlkit"
    uv run python demo/sql/...

Regression suite del porting (deve restare verde):

    uv run python test/regress_porting_traps/run_all.py

Atteso: 41 passed con `appy` installato; 39 passed + 2 skipped senza
(`appy` è optional, vedi sotto).

Test, demo e screenshot che creano widget GTK vanno eseguiti in un display
virtuale isolato, mai sul desktop dell'utente:

    env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a uv run pytest -q
    env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a uv run python test/regress_porting_traps/run_all.py

`xvfb-run` da solo non basta: con `WAYLAND_DISPLAY` impostato GTK sceglie il
backend Wayland e apre le finestre sulla sessione reale, ignorando Xvfb (e la
cattura di Xvfb esce nera). Vale anche per le applicazioni che usano sqlkit
(es. pysia) e va ripetuto nei prompt dei subagenti.

Note operative
--------------

* Mercurial, non git: usare solo `hg` per VCS.
* `pyproject.toml` è la fonte di verità per metadata, dipendenze e
  configurazione Babel (`[tool.babel.*]`).
* Dipendenze di sviluppo dichiarate in `[dependency-groups] dev`
  (PEP 735): installate da `uv sync` (gruppo `dev` di default).
* `appy` (printing engine) è optional: `uv sync --extra printing`
  oppure `pip install sqlkit[printing]` per abilitarlo.
