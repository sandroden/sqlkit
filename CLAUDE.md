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

Regression suite del porting (deve restare verde, atteso 41 passed):

    uv run python test/regress_porting_traps/run_all.py

Note operative
--------------

* Mercurial, non git: usare solo `hg` per VCS.
* Topic attivo per i lavori di setup/build: `uv-finalization`.
* `pyproject.toml` è la fonte di verità per metadata, dipendenze e
  configurazione Babel (`[tool.babel.*]`).
* Dipendenze di sviluppo dichiarate in `[dependency-groups] dev`
  (PEP 735): installate da `uv sync` (gruppo `dev` di default).
