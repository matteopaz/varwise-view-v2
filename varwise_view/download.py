import os
import requests
import pandas as pd
from io import StringIO
from pathlib import Path
from typing import Optional, Union
from . import CATALOG_URL, PURE_CATALOG_URL, DATA_URL
from .paths import get_data_dir
import subprocess

def acquire_catalog(
    pure: bool = False,
    force: bool = False,
):
    """Downloads the compressed catalog from the remote server."""

    base = get_data_dir()
    catalog_path = base / ("catalog.csv" if not pure else "pure_catalog.csv")
    url = CATALOG_URL if not pure else PURE_CATALOG_URL

    # Skip download if the catalog already exists and not forcing
    if not force and catalog_path.exists():
        print("Catalog already downloaded.")
        return

    print(f"Downloading VarWISE catalog{' (pure)' if pure else ''}... Should take less than a minute.")
    response = requests.get(url)
    response.raise_for_status()
    content = response.content

    catalog = pd.read_csv(StringIO(content.decode('utf-8')), compression='infer')

    catalog.to_csv(str(catalog_path), index=False)

def acquire_data(
    force: bool = False
):
    """Downloads the compressed parquet data from the remote server."""

    base = get_data_dir()
    data_path = base / "data.tar.gz"

    if not force:
        if data_path.exists():
            print("Data already downloaded.")
            return

    print("Downloading VarWISE data (tar.gz)... This may take a while.")
    subprocess.run([
        "curl", "-L", DATA_URL, "-o", str(data_path)
    ], check=True)

    print("Extracting data...")
    subprocess.run([
        "tar", "-xzf", str(data_path), "-C", str(base)
    ], check=True)

    print("Done!")
    


if __name__ == "__main__":
    acquire_catalog()
    acquire_data()
