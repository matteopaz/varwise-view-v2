# Architecture Overview
## Purpose
VarWISE View is a Flask webapp and CLI for exploring a ~2M-row astronomy catalog and per-object observation data. It balances client-side rendering with server-side data access to stay responsive on large datasets.
## Components
- Server (`Flask`): `varwise_view/app.py` exposes routes, prepares JSON for charts, serves templates/assets.
- Core logic: `varwise_view/core.py` loads the catalog, queries parquet data via `pyarrow.dataset`, and builds Plotly figures.
- CLI: `varwise_view/cli.py` provides `varwise-view` with `--port` and `--pure`, bootstraps downloads, then runs the server.
- Data acquisition: `varwise_view/download.py` downloads catalog CSV and a tarball of parquet data using `requests`/`curl` and extracts it.
- Paths: `varwise_view/paths.py` resolves the writable data directory (`VARWISE_VIEW_DATA_DIR` or per-user path).
## Data Flow
1) Catalog: CSV loaded by `pandas` in `get_catalog(pure=False)` and indexed by `cluster_id`.
2) Observations: Parquet dataset opened via `pyarrow.dataset.dataset(base/data, format="parquet")` and filtered on:
   - `partition` = `cluster_id >> 48`
   - `cluster_id` = requested object id
3) Server prepares Plotly-ready JSON for W1, W2, and W1−W2 series with errors; client renders via Plotly in templates.
## Routes
- `/`: Loads catalog into the page (JSON-serialized) for quick perusal and client interactions.
- `/object/<int:cid>`: Fetches observation rows for a single object, returns detail view with plots and CSV download data.
## Performance & Reliability
- Arrow dataset handle is cached to avoid repeated scans; filters push down to parquet.
- Heavy rendering stays client-side (Plotly); server limits work to data access/serialization.
- Downloads and extracted data live in `VARWISE_VIEW_DATA_DIR`; package `assets/` is read-only.
## Extensibility
- Add new endpoints in `app.py`; keep computation in `core.py`.
- For querying/filtering, prefer Arrow/pandas operations server-side and keep charting on the client.
