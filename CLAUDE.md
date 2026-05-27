# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

A tool for authoring Scottish Country Dances. The same data model (Figure JSON files in `Figures/`, Dance JSON files in `Dances/`) is consumed by two parallel runtimes:

1. **CLI / simulator** — `DanceCreator.py` loads a dance, walks its figures, mutates a `DanceFloor`, and prints textual "crips" (cues) per bar. This is the original engine.
2. **Flask web GUI** — `GUI_DanceCreator_App.py` serves `templates/index.html` plus a JSON API. The GUI is an authoring/inspection front-end; it does **not** yet share code with the simulator — it only reads the same JSON files.

UI strings, comments, and most identifiers are German. Class/method names and JSON keys are English.

## Commands

```bash
# Activate the in-repo venv (Python 3.13)
source .venv/bin/activate

# Install the only dependency (no requirements.txt exists)
pip install flask

# Run the web GUI → http://127.0.0.1:5000
python GUI_DanceCreator_App.py

# Run the CLI simulator (prints the floor + crips for "Marries Wedding")
python DanceCreator.py

# Smoke-test the /figures endpoint without starting a server
python check_figures_api.py
```

There is no test suite, linter, or build step. `check_figures_api.py` is the closest thing to a test — it uses Flask's `test_client` to assert `/figures` returns parseable JSON.

## Figure / Dance JSON model

Everything in `Figures/*.json` and `Dances/*.json` follows one of two shapes, distinguished by the `Version` field and by which keys are present:

- **Simple figure (`Version: 2`)** — leaf node. Has `StartPos`, `EndPos`, `Bars`, `CriptDesc`, optionally `Faceing`, `Partner`, `Addons`. Loaded by `SimpleFigure`.
- **Complex figure / Dance (`Version: 3`)** — composite. Has a `FigureList` instead of positions. Loaded by `ComplexFigure`. Dances are just complex figures stored in `Dances/`.

`FigureList` uses a small ad-hoc DSL — read `ComplexFigure.loadSubFigure` and `Marries Wedding_all.json` together to understand it:

- `["s", [child, child, ...]]` — **sequential**: dance children one after another, accumulating bars.
- `["p", [child, child, ...]]` — **parallel**: dance children simultaneously; all must have the same bar count, results combined via `DanceFloor.combineDanceFloor`.
- `[[row, col], "FigureName"]` or `[[row, col], ["FigureName", ["AddonKey", ...]]]` — a leaf reference to a `Figures/*.json` file, anchored at `(row, col)`.

The anchor is added to every `StartPos`/`EndPos`/`Facing`/`Partner` coordinate via `Figure.posWithAnchor`. This is how the same `1cRT` figure can be reused at couple 1, 2, or 3.

**Addons** (`Version: 1`) live inside a Simple figure's `Addons` dict. They override specific positions or crip strings of the host figure — see `Figures.FigureAddon` and how `SimpleFigure` calls `Addon.StartPos(...)`, `Addon.EndPos(...)`, etc. in property getters to layer the overrides. Addon selection is per-invocation (the second element of the leaf tuple, e.g. `["H1DR", ["E2c"]]`).

**Crip templating** — `CriptDesc` strings contain placeholders that `SimpleFigure.getCrips` substitutes against the live `DanceFloor`:
- `{Dancer}` → dancer name at `StartPos`
- `{StartPos}` / `{EndPos}` → human-readable position name
- `{Face}` → position name from `_FacingPos`
- `{Partner}` → dancer name from `_PartnerPos`

Unsubstituted placeholders that have no data raise exceptions — they are not silently dropped.

`Figures/figure.schema.json` exists but is **incomplete and slightly out of sync** with the loader (e.g. it requires `Formation` which the Python loaders don't check, and it predates some Version bumps). Treat the schema as advisory; trust the loaders.

## Flask app architecture

`GUI_DanceCreator_App.py` is intentionally thin and stateful:

- `Figure_DB` is a module-level dict populated once by `load_Figuers()` at startup (reads every `Figures/*.json`). Restart the server after adding new figures.
- `/figures` returns the full `Figure_DB` as an array, sorted by name — the GUI uses this to render the left-column cards.
- `/tree?file=NAME.json` reads a file from `Figures/` or `Dances/` and returns a **flat** node list (`id`, `parent_id`, `name`, `meta`) via `build_tree_from_json`. This is a fallback parser; it does not yet expand `FigureList` recursively into a real tree.
- `/dances` lists available dance files for the Load dialog.
- `/get_nodes/<name>` is a stub used for lazy children expansion.

The front-end (`templates/index.html`) is one big inline-script page that:
- Initializes a hardcoded jsTree on first load (`populateJsTree`) — this is sample data, not real content from `/tree`.
- Renders draggable figure cards from `/figures` and supports drag-into-jsTree via the `application/x-figure` MIME type.
- Implements its own resizable three-pane layout via `makeSplitter`.

`static/Cards.js`, `static/DC.js`, `static/Tree.js`, `static/app.js`, `static/resize.js` are mostly empty or placeholder — the real logic lives inline in `index.html`. When extracting, prefer moving code into these files rather than creating new ones.

## Things to know before editing

- The CLI engine and the Flask GUI **do not yet share code**. `SimpleFigure`/`ComplexFigure` are not imported by `GUI_DanceCreator_App.py`; the GUI parses JSON ad-hoc. Don't assume edits to the loader affect the web side or vice versa.
- `Dance.getFigure` and `ComplexFigure.loadFigure` both build paths with `os.getcwd()` (not `__file__`) — they only work when run from the repo root.
- `SimpleFigure._Partner`, `_CriptDesc`, `_Addons` are declared as **class** attributes but mutated as instance state in `clear()`. Be careful adding new list-typed fields — follow the same `clear()` pattern to avoid cross-instance leakage.
- Version mismatches raise exceptions rather than attempting migration. When bumping a figure to a new `Version`, also update the check in the corresponding loader (`SimpleFigure.loadFigure` checks `2`, `ComplexFigure.loadFigure` checks `3`, `FigureAddon.loadAddon` checks `1`).
