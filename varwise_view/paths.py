from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union
import importlib.resources as resources
from platformdirs import user_data_dir


def get_assets_dir() -> Path:
    """Return the package-scoped assets directory path.

    Only for read-only, packaged resources. Do not write here.
    """
    pkg_root = Path(resources.files("varwise_view"))
    return pkg_root / "assets"


def get_data_dir() -> Path:
    """Return the writable data directory to store downloads.

    Resolution order:
    1) Environment variable `VARWISE_VIEW_DATA_DIR`
    2) OS-appropriate per-user data dir via platformdirs
    """

    env = os.getenv("VARWISE_VIEW_DATA_DIR")
    if env:
        path = Path(env)
    else:
        path = Path(user_data_dir(appname="varwise-view", appauthor="VarWISE"))
    path.mkdir(parents=True, exist_ok=True)
    return path
