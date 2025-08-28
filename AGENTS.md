# Repository Guidelines

## Project Structure & Module Organization
- `varwise_view/`: Python package
  - `app.py`: Flask routes and rendering
  - `core.py`: catalog I/O, parquet access, plotting helpers
  - `cli.py` / `__main__.py`: entrypoint (`varwise-view`) and flags
  - `download.py`: data/catalog download & extraction
  - `paths.py`: data/asset path resolution (`VARWISE_VIEW_DATA_DIR`)
  - `templates/`, `static/`: HTML UI and assets
  - `assets/`: packaged sample data (not writable)
- No `tests/` folder yet.

## Build, Test, and Development Commands
- Install (editable): `pip install -e .`
  - Installs CLI `varwise-view` and dependencies from `pyproject.toml`.
- Run locally: `varwise-view --port 9000 [--pure]`
  - Downloads catalog/data on first run, then starts Flask at `http://localhost:9000`.
- Alternate run: `python -m varwise_view --port 9000 [--pure]`
- Set data dir (optional): `export VARWISE_VIEW_DATA_DIR=/path/to/data`
  - Overrides default per-user data location.

## Coding Style & Naming Conventions
- Python, PEP 8, 4-space indentation; include type hints where practical.
- Names: modules and functions `snake_case`; constants `UPPER_CASE` (see `__init__.py`); classes `CamelCase`.
- Prefer small, pure helpers in `core.py`; keep Flask specifics in `app.py`.
- Formatting: use `black` and `isort` if available; no strict config enforced yet.

## Testing Guidelines
- Framework: not yet configured. If adding tests, use `pytest`.
- Naming: `tests/test_*.py`; keep unit tests close to module seams (`core.py`, `paths.py`).
- Data-dependent tests: mock filesystem via `VARWISE_VIEW_DATA_DIR` and small sample parquet/csv fixtures.

## Commit & Pull Request Guidelines
- Commits: short, imperative subject lines (e.g., "Add gaia overlay"). Keep scope-focused.
- PRs: include description, steps to run, screenshots/GIFs for UI changes, and linked issues (e.g., `Closes #12`).
- CI not configured; please run app locally before requesting review.

## Security & Configuration Tips
- Downloads use remote URLs defined in `varwise_view/__init__.py`; verify before changing.
- Requires `curl` and `tar` on PATH for data acquisition.
- Do not write into `varwise_view/assets`; writable cache lives under `VARWISE_VIEW_DATA_DIR`.
