import concurrent.futures
import argparse

from . import DEFAULT_PORT
from .app import create_app
from .download import acquire_catalog, acquire_data


def main():
    """Console entrypoint to run the VarWISE View server.

    - If `preload` is True, pre-cache all objects before starting.
    - Always start background sideloader threads to keep cache warm.
    - Then run the Flask development server.
    """

    parser = argparse.ArgumentParser(
        description="Run the VarWISE View web application."
    )

    parser.add_argument(
        "-p", "--port", type=int, default=DEFAULT_PORT,
        help="Port to run the server on (default: 9000)."
    )

    parser.add_argument(
        "-r", "--reload", action='store_true', default=False,
        help="Force reload/redownload of the catalog"
    )

    args = parser.parse_args()
    port = args.port
    force_reload = args.reload
    
    # Always acquire both catalogs to support runtime toggling in the UI
    acquire_catalog(pure=True, force=force_reload)
    acquire_catalog(pure=False, force=force_reload)
    acquire_data()

    # Propagate flags into the app config
    app = create_app()

    app.run(port=port, debug=True)


if __name__ == "__main__":
    main()
