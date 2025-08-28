"""VarWISE View package.

This package provides tools to filter VarWISE catalogs and a Flask app
to browse lightcurves. Configuration variables are exposed at package level.
"""

# Package metadata
__version__ = "0.1.0"

# App configuration
DEFAULT_PORT = 9000  # Default localhost port for the app

# PAGINATION
PAGINATION_UNIT = 20

# Placeholders (do not change)
CATALOG_URL = "https://app.box.com/index.php?rm=box_download_shared_file&shared_name=krzguzne4o5ok1w8xohc4fcvnsee7ws5&file_id=f_1964687262737"
PURE_CATALOG_URL = "https://app.box.com/index.php?rm=box_download_shared_file&shared_name=aumvzn88yfnmudvmsyds5av9eqhzbqga&file_id=f_1964679887806"
DATA_URL = "https://app.box.com/index.php?rm=box_download_shared_file&shared_name=9o4x9wbno3axd7phmyg8jfeuwj65gj1r&file_id=f_1967074780605"

__all__ = [
    "__version__",
    "port",
    "preload",
    "sideloader_threads",
    "query_radius",
    "USE_PURE_CATALOG",
    "QUERY",
    "SORTBY",
    "ROWLIMIT",
    "CATALOG_URL",
    "DATA_URL",
]

