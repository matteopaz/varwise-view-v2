"""Backend entrypoint used by the desktop app bundle.

This intentionally avoids Flask debug/reload behavior so the Electron wrapper can
own the process lifecycle cleanly.
"""

from __future__ import annotations

import argparse
import os
import sys

from varwise_view.app import create_app
from varwise_view.download import acquire_catalog, acquire_data
from varwise_view import DEFAULT_PORT


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the VarWISE View desktop backend.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--reload-data",
        action="store_true",
        help="Force redownload of catalog files before starting.",
    )
    args = parser.parse_args()

    # Helps Python emit useful first-run progress to the Electron loading screen.
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

    os.environ.setdefault("VARWISE_VIEW_DESKTOP", "1")

    print("Preparing VarWISE data cache...")
    acquire_catalog(pure=True, force=args.reload_data)
    acquire_catalog(pure=False, force=args.reload_data)
    acquire_data()

    print(f"Starting VarWISE View on http://{args.host}:{args.port}")
    app = create_app()
    app.run(
        host=args.host,
        port=args.port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()
