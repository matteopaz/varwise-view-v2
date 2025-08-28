# VarWISE View

Lightweight Flask web app and CLI to explore the VarWISE catalog (Paz et al., 2025 in prep) and per-object WISE lightcurves.

**Features**
- **Catalog browser:** Paginated, server-side filtering and sorting across ~2M rows.
- **Pure/full toggle:** Switch between the “pure” and full catalogs via UI or `?pure=1|0`.
- **Object view:** Plot W1, W2, and color (W1−W2) with errors; interactive phase folding.
- **Column control:** Toggle visible columns and persist preferences locally.
- **ZTF overlay:** Async fetch of nearby ZTF lightcurves (`/api/ztf`).

**Quickstart**
- **Python:** `>=3.9`
- **Install (editable):** `pip install -e .`
- **Run:** `varwise-view --port 9000`
  - First run downloads the catalog(s) and a tarball of parquet data, then starts Flask at `http://localhost:9000`.

**Data & Paths**
- **Writable cache:** `VARWISE_VIEW_DATA_DIR` or per-user data dir (via `platformdirs`).
- **Set explicitly:** `export VARWISE_VIEW_DATA_DIR=/path/to/data`
- **Requirements:** `curl` and `tar` on `PATH` for data acquisition.
- **Do not write:** `varwise_view/assets` (packaged, read-only).

**CLI & URLs**
- **CLI:** `varwise-view [-p | --port PORT]`
- **Module:** `python -m varwise_view --port 9000`
- **Catalog toggle:** add `?pure=1` (pure) or `?pure=0` (full) to page URLs.
- **Filter grammar:** comma-separated clauses: `<column> <op> <number|"string">` where `<op>` in `> >= < <= == != =`.

**Key Endpoints**
- `/` – Catalog table (server-side pagination, filtering, sorting).
- `/object/<cluster_id>` – Detail view and plots for a single object.
- `/api/catalog` – JSON for DataTables server-side protocol; supports `filter`, `order_col`, `order_dir`.
- `/api/ztf?ra=..&dec=..&rad=..` – Nearby ZTF lightcurve columns (default: `mag,magerr,mjd`).

**Repository Layout**
- `varwise_view/app.py` – Flask routes and rendering.
- `varwise_view/core.py` – Catalog I/O, parquet access, plotting helpers.
- `varwise_view/cli.py` / `__main__.py` – Entrypoint and flags.
- `varwise_view/download.py` – Catalog/data download & extraction.
- `varwise_view/paths.py` – Writable data dir resolution.
- `varwise_view/templates/`, `static/` – HTML UI and assets.