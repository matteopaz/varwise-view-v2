# Overview

This is a webapp/cli tool to easily analyze an astronomy catalog of objects. We want to analyze a long, many-columned catalog of data of about 2M rows, able to peruse it quickly with queries, and analyze its observation data (object.j2 template and related endpoints). This app should strike a balance between clientside and serverside compute weight.

# Installation

Clone this repository:

```git clone https://github.com/matteopaz/varwise-view.git```

Install the required packages:
```
pip install astroquery astropy
pip install plotly joblib pandas numpy pandasql
pip install flask
```

# Setup
First, you will need the VarWISE and VarWISE pure catalogs. Place those `csv` files into the `/varwise_cats/` directory as titled `VarWISE` and `pure_VarWISE`.

In `__init__.py`, define the `QUERY` SQL constraint and run `python filter.py`, which will produce a subset of either VarWISE or VarWISE pure, saving it to `catalog.csv`. You may also place your own subcatalog in place of this generated file.


# Running
- Start the server: `varwise-view` (or `python -m varwise_view`)
- Open: `http://localhost:9000`

Light mode is strongly recommended.
