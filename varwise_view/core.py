import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset
import requests
from plotly import graph_objects as go
from .paths import get_data_dir
import astropy
from astropy.io import votable
from io import BytesIO

def get_catalog(pure=False) -> pd.DataFrame:
    try:
        base = get_data_dir()
        path = base / ("pure_catalog.csv" if pure else "catalog.csv")
        catalog = pd.read_csv(str(path)).set_index("cluster_id")
    except FileNotFoundError:
        raise RuntimeError(
            "Catalog file not found. Please run the CLI to acquire data first."
        )
    return catalog

_DATASET = None
_DATASET_PATH = None


def _get_dataset(base_path: str):
    """Return a cached pyarrow dataset for the parquet data directory."""
    global _DATASET, _DATASET_PATH
    if _DATASET is not None and _DATASET_PATH == base_path:
        return _DATASET
    # (Re)initialize dataset if first time or path changed
    _DATASET = pyarrow.dataset.dataset(base_path, format="parquet", partitioning="hive")
    _DATASET_PATH = base_path
    return _DATASET

def query_ztf_data(ra: float, dec: float, rad: float, cols: list[str]=["mag", "magerr", "mjd"]):
    """
    Query the ZTF data at (RA, Dec) with a radius of rad in arcsec.
    """
    qstring = f"https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE {ra} {dec} {rad/3600}"
    qstring += "&BAD_CATFLAGS_MASK=32768"
    
    res = requests.get(qstring)
    res.raise_for_status()

    content = res.content

    astrotbl = votable.parse_single_table(BytesIO(content)).to_table()
    tbl = astrotbl.to_pandas()

    out = {col: np.array(tbl[col].values) for col in cols}

    return out

def get_object_data(cid: int):
    partition = cid >> 48  # leftmost 16 out of 64 bits are an int

    base = get_data_dir()
    ds_path = base / f"data/"
    try:
        ds = _get_dataset(str(ds_path))

        partition_filter = pc.equal(pc.field("partition"), partition)
        cid_filter = pc.equal(pc.field("cluster_id"), cid)

        complete_filter = partition_filter & cid_filter

        df = ds.to_table(filter=complete_filter).to_pandas()

        df.set_index("cluster_id", inplace=True)

        if df.empty:
            raise ValueError("No data found for the given cluster ID.")
        if df.shape[0] > 1:
            raise ValueError("Multiple entries found for the given cluster ID.")
        
        object = df.iloc[0].copy()

        # Converting flux to mag

        object['w1mag'] = -2.5 * np.log10(object['w1flux']*0.00000154851985514 / 309.54) 
        object['w2mag'] = -2.5 * np.log10(object['w2flux']*0.00000249224248693 / 171.787) 
        object['w1sigmag'] = (2.5 / np.log(10)) * (object['w1sigflux'] / object['w1flux'])
        object['w2sigmag'] = (2.5 / np.log(10)) * (object['w2sigflux'] / object['w2flux'])

    except FileNotFoundError:
        raise RuntimeError(
            "Object data file not found. Please run the CLI to acquire data first."
        )
    return object