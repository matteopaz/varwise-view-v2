import os
import tarfile
import requests
import pandas as pd
from io import StringIO
from pathlib import Path
from typing import Optional, Union
from . import CATALOG_URL, PURE_CATALOG_URL, DATA_URL
from .paths import get_data_dir


def acquire_catalog(
    pure: bool = False,
    force: bool = False,
):
    """Downloads the compressed catalog from the remote server."""

    base = get_data_dir()
    base.mkdir(parents=True, exist_ok=True)
    catalog_path = base / ("catalog.csv" if not pure else "pure_catalog.csv")
    url = CATALOG_URL if not pure else PURE_CATALOG_URL

    # Skip download if the catalog already exists and not forcing
    if not force and catalog_path.exists():
        print("Catalog already downloaded.")
        return

    print(f"Downloading VarWISE catalog{' (pure)' if pure else ''}... Should take less than a minute.")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    content = response.content

    catalog = pd.read_csv(StringIO(content.decode('utf-8')), compression='infer')

    catalog.to_csv(str(catalog_path), index=False)


def _safe_extract_tar_gz(archive_path: Path, destination: Path) -> None:
    """Extract a tar.gz archive while preventing path traversal."""
    destination = destination.resolve()

    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            target_path = (destination / member.name).resolve()
            if destination not in target_path.parents and target_path != destination:
                raise RuntimeError(f"Unsafe path in archive: {member.name}")
        archive.extractall(destination)


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".part")

    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with tmp_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    tmp_path.replace(destination)


def acquire_data(
    force: bool = False
):
    """Downloads and extracts the compressed parquet data from the remote server."""

    base = get_data_dir()
    base.mkdir(parents=True, exist_ok=True)
    data_path = base / "data.tar.gz"

    if not force and data_path.exists():
        print("Data already downloaded.")
        return

    print("Downloading VarWISE data (tar.gz)... This may take a while.")
    _download_file(DATA_URL, data_path)

    print("Extracting data...")
    _safe_extract_tar_gz(data_path, base)

    print("Done!")
    


if __name__ == "__main__":
    acquire_catalog(pure=False, force=True)
    acquire_catalog(pure=True, force=True)
    acquire_data(force=True)
