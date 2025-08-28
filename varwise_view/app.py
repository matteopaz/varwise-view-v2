import numpy as np
import pandas as pd
import plotly.graph_objects as go
from flask import Flask, render_template, send_from_directory, request, jsonify
from .core import get_catalog, get_object_data, query_ztf_data
from . import PAGINATION_UNIT
from json import dumps
import os
from typing import Optional
 

CATALOG_PURE = None
CATALOG_FULL = None

app = Flask(__name__, template_folder="templates", static_folder="static")

def create_app(use_pure: Optional[bool] = None, data_dir: Optional[str] = None):
    """Application factory returning the configured Flask app.

    Routes are bound at import-time, so this simply returns the module-level
    `app` instance for WSGI servers or external runners.
    """

    global CATALOG_PURE, CATALOG_FULL, _DATA_DIR_OVERRIDE
    _DATA_DIR_OVERRIDE = data_dir
    # Preload both catalogs for runtime switching via query param
    CATALOG_PURE = get_catalog(True)
    CATALOG_FULL = get_catalog(False)

    return app


def _is_pure_request() -> bool:
    """Determine if current request should use the pure catalog.

    Defaults to True when unspecified.
    """
    try:
        flag = request.args.get('pure')
        if flag is None:
            return True
        return str(flag) not in ('0', 'false', 'False')
    except Exception:
        return True


def _current_catalog():
    return CATALOG_PURE if _is_pure_request() else CATALOG_FULL


def _apply_filter(df: pd.DataFrame, filter_str: Optional[str]):
    """Apply a simple comma-separated constraint list to a DataFrame.

    Grammar per clause: <column> <op> <number or "string">
    - op in {>, >=, <, <=, ==, !=, =}
    - values: integers, floats, scientific notation, or quoted strings ("abc")
    - Clauses separated by commas; combined with logical AND.

    Returns (filtered_df, filtered_count). Raises ValueError on invalid input.
    """
    if not filter_str:
        return df, len(df)

    clauses = [c.strip() for c in filter_str.split(',') if c.strip()]
    if not clauses:
        return df, len(df)

    mask = pd.Series(True, index=df.index)

    import operator as op

    ops = {
        '>': op.gt,
        '>=': op.ge,
        '<': op.lt,
        '<=': op.le,
        '==': op.eq,
        '!=': op.ne,
        '=': op.eq,
    }

    import re

    # Accept quoted strings as values for equality/inequality
    pattern = re.compile(
        r'^\s*([A-Za-z_][A-Za-z0-9_?()\-]*)\s*(<=|>=|==|!=|<|>|=)\s*('
        r'[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|"[^"]*")\s*$'
    )

    for clause in clauses:
        m = pattern.match(clause)
        if not m:
            raise ValueError(f"Invalid clause: '{clause}'")
        col, op_sym, val_str = m.groups()
        if col not in df.columns:
            raise ValueError(f"Unknown column: '{col}'")
        fn = ops[op_sym]

        # Check for quoted string
        if val_str.startswith('"') and val_str.endswith('"'):
            if op_sym not in ('==', '!=', '='):
                raise ValueError(f"String comparison only allowed with ==, !=, =: '{clause}'")
            value = val_str[1:-1]
            series = df[col].astype(str)
            clause_mask = fn(series, value)
        else:
            try:
                value = float(val_str)
            except Exception:
                raise ValueError(f"Invalid number in clause: '{clause}'")
            series = pd.to_numeric(df[col], errors='coerce')
            clause_mask = fn(series, value)
            clause_mask = clause_mask.fillna(False)

        mask &= clause_mask

    filtered = df[mask]
    return filtered, int(mask.sum())


@app.route("/")
def idx():
    # Only send column names and metadata; data will be fetched via server-side pagination
    cat = _current_catalog()
    cols = list(cat.reset_index().columns)
    cols_json = dumps(cols)
    total_rows = len(cat)
    # Pass through any filter in query string to initialize UI
    initial_filter = request.args.get('filter', '')
    initial_pure = _is_pure_request()
    return render_template(
        "index.j2",
        cols=cols_json,
        page_size=PAGINATION_UNIT,
        total_rows=total_rows,
        initial_filter=initial_filter,
        initial_pure=initial_pure,
    )


@app.get('/api/catalog')
def api_catalog():
    cat = _current_catalog()
    # Support DataTables server-side protocol if 'draw' is present; otherwise simple paging
    if 'draw' in request.args:
        try:
            draw = int(request.args.get('draw', '1'))
            start = int(request.args.get('start', '0'))
            length = int(request.args.get('length', str(PAGINATION_UNIT)))
        except ValueError:
            return jsonify({"error": "Invalid parameters"}), 400

        total = len(cat)
        if start < 0: start = 0
        if length < 1: length = PAGINATION_UNIT
        end = start + length

        base = cat.reset_index()
        # Optional filtering
        filter_q = request.args.get('filter')
        try:
            filtered_df, filtered_count = _apply_filter(base, filter_q)
        except ValueError as e:
            return jsonify({"error": f"Invalid filter: {e}"}), 400

        # Optional ordering across the entire filtered set
        order_col = request.args.get('order_col')
        order_dir = request.args.get('order_dir', 'asc')
        if order_col:
            if order_col not in filtered_df.columns:
                return jsonify({"error": f"Invalid sort column: {order_col}"}), 400
            ascending = (order_dir != 'desc')
            # Use pandas sort_values; stable sort to preserve order for ties
            try:
                filtered_df = filtered_df.sort_values(by=order_col, ascending=ascending, kind='mergesort')
            except Exception:
                # Fallback: attempt numeric sort if column is mixed-type
                try:
                    temp = pd.to_numeric(filtered_df[order_col], errors='coerce')
                    filtered_df = filtered_df.assign(_ord=temp).sort_values(by="_ord", ascending=ascending, kind='mergesort').drop(columns=["_ord"]) 
                except Exception:
                    pass

        df = filtered_df.iloc[start:end].copy()
        df["cluster_id"] = df["cluster_id"].astype(str)
        # Ensure strict JSON compatibility: replace NaN/Inf with None (null)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.where(pd.notnull(df), None)
        rows = df.to_dict(orient="records")
        return jsonify({
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": filtered_count,
            "data": rows,
        })
    else:
        # Simple page/limit mode
        try:
            page = int(request.args.get('page', '1'))
            limit = int(request.args.get('limit', str(PAGINATION_UNIT)))
        except ValueError:
            return jsonify({"error": "Invalid page or limit"}), 400

        if page < 1 or limit < 1:
            return jsonify({"error": "page and limit must be positive"}), 400

        start = (page - 1) * limit
        end = start + limit

        base = cat.reset_index()
        filter_q = request.args.get('filter')
        try:
            filtered_df, filtered_count = _apply_filter(base, filter_q)
        except ValueError as e:
            return jsonify({"error": f"Invalid filter: {e}"}), 400

        # Optional ordering across the entire filtered set
        order_col = request.args.get('order_col')
        order_dir = request.args.get('order_dir', 'asc')
        if order_col:
            if order_col not in filtered_df.columns:
                return jsonify({"error": f"Invalid sort column: {order_col}"}), 400
            ascending = (order_dir != 'desc')
            try:
                filtered_df = filtered_df.sort_values(by=order_col, ascending=ascending, kind='mergesort')
            except Exception:
                try:
                    temp = pd.to_numeric(filtered_df[order_col], errors='coerce')
                    filtered_df = filtered_df.assign(_ord=temp).sort_values(by="_ord", ascending=ascending, kind='mergesort').drop(columns=["_ord"]) 
                except Exception:
                    pass

        df = filtered_df.iloc[start:end].copy()
        df["cluster_id"] = df["cluster_id"].astype(str)
        # Ensure strict JSON compatibility: replace NaN/Inf with None (null)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.where(pd.notnull(df), None)
        rows = df.to_dict(orient="records")

        return jsonify({
            "data": rows,
            "page": page,
            "limit": limit,
            "total_rows": filtered_count,
        })


@app.route('/object/<int:cid>')
def getobject(cid: int):
    cat = _current_catalog()
    if cid not in cat.index:
        return "Not found", 404
    
    # Getting assets
    catalog_row = cat.loc[cid]
    column_map = {c: catalog_row[c] for c in catalog_row.index} # To display all columns in template
    column_map = {c: v.item() if isinstance(v, np.generic) else v for c, v in column_map.items()}
    data_row = get_object_data(cid)

    # Plotting lightcurve (server-side only for the full, non-folded view)
    title = catalog_row["Designation"]

    dfpd = catalog_row["period_peak_1"]
    if not (dfpd > 0):  # if period is not available, set default period to 4000 days
        dfpd = 4000.0

    # Raw series for client-side phase folding
    lc_series = dumps({
        "t": data_row["mjd"].tolist(),
        "w1": data_row["w1mag"].tolist(),
        "w1s": data_row["w1sigmag"].tolist(),
        "w2": data_row["w2mag"].tolist(),
        "w2s": data_row["w2sigmag"].tolist(),
    })

    # Previous and next object IDs for navigation
    # Determine prev/next within current catalog
    cids = cat.index.tolist()
    cid_positions = {cid_: i for i, cid_ in enumerate(cids)}
    idx_ = cid_positions.get(cid)
    if idx_ is None:
        return "Not found", 404
    previd = str(cids[(idx_ - 1) % len(cids)])
    nextid = str(cids[(idx_ + 1) % len(cids)])

    return render_template(
        "object.j2",
        titletext=title,
        lc_series=lc_series,
        columns=column_map,
        prev_id=previd,
        next_id=nextid,
        prevnext=[previd, nextid],
        defaultperiod=dfpd,
    )


# just for favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )


@app.get('/api/ztf')
def api_ztf():
    """Return ZTF lightcurve near a sky position using query_ztf_data.

    Query params:
    - ra: float, degrees
    - dec: float, degrees
    - rad: float, arcseconds (optional, default 5.0)
    - cols: comma-separated list (optional, default: mag,magerr,mjd)
    """
    ra_s = request.args.get('ra')
    dec_s = request.args.get('dec')
    if ra_s is None or dec_s is None:
        return jsonify({"error": "Missing ra/dec"}), 400
    try:
        ra = float(ra_s)
        dec = float(dec_s)
    except ValueError:
        return jsonify({"error": "Invalid ra/dec"}), 400

    rad_s = request.args.get('rad', '5.0')
    try:
        rad = float(rad_s)
    except ValueError:
        return jsonify({"error": "Invalid rad"}), 400

    cols_param = request.args.get('cols', 'mag,magerr,mjd')
    cols = [c.strip() for c in cols_param.split(',') if c.strip()]

    try:
        data = query_ztf_data(ra=ra, dec=dec, rad=rad, cols=cols)
    except Exception as e:
        return jsonify({"error": f"ZTF query failed: {str(e)}"}), 502

    # Convert numpy arrays to lists for JSON
    out = {k: (v.tolist() if hasattr(v, 'tolist') else list(v)) for k, v in data.items()}
    return jsonify(out)
