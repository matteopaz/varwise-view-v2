# VarWISE View Desktop

This directory contains the one-click desktop wrapper for VarWISE View.

The desktop app keeps the existing Flask application intact. PyInstaller freezes `desktop/backend_launcher.py` into a local backend executable. Electron starts that backend on `127.0.0.1` using a free local port, then opens a desktop window pointed at the local Flask app. On first launch, the backend downloads the catalog and light-curve data into the user's local VarWISE cache.

Users do not need Python, Node, Git, Docker, or a terminal.

## Build artifacts

GitHub Actions builds macOS `.dmg` / `.zip` artifacts and Windows installer / portable `.exe` artifacts.

Run the workflow from GitHub Actions using the `Build desktop app` workflow. Artifacts are uploaded at the end of the workflow run.

## Local development

Install the Python package and Electron dependencies:

```bash
python -m pip install -e .
npm install
```

Run the Electron wrapper against the live Python backend launcher:

```bash
npm run desktop:dev
```

## Local packaged build

Install build dependencies:

```bash
python -m pip install -e . pyinstaller
npm install
```

Freeze the Python backend:

```bash
pyinstaller --clean --noconfirm desktop/pyinstaller/varwise-view-backend.spec
```

Then build the desktop app:

```bash
npm run dist:mac
npm run dist:win
```

Outputs appear in `release/`.

## Notes

- The app is unsigned, so macOS may require manual approval the first time it opens.
- First launch can take a while because data is downloaded and extracted locally.
- Data is stored in `VARWISE_VIEW_DATA_DIR` when set, otherwise in the per-user app data directory resolved by `platformdirs`.
- The backend binds only to `127.0.0.1`, so it is not exposed on the LAN.
