"""Download monthly NASA POWER data and return clean pandas objects."""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
FILL_VALUE = -999.0  # NASA POWER's code for "no data"


def fetch_point(parameter: str, lat: float, lon: float,
                start_year: int, end_year: int,
                use_cache: bool = True) -> pd.Series:
    """Monthly time series for ONE location, indexed by the first day of each month."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{parameter}_{lat:.2f}_{lon:.2f}_{start_year}_{end_year}.csv"

    # 1) Cache hit: skip the network entirely
    if use_cache and cache_file.exists():
        series = pd.read_csv(cache_file, index_col=0, parse_dates=True).iloc[:, 0]
        series.name = parameter
        return series

    # 2) Otherwise ask NASA
    params = {
        "parameters": parameter,
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": start_year,
        "end": end_year,
        "format": "JSON",
    }
    response = requests.get(BASE_URL, params=params, timeout=60)
    response.raise_for_status()  # raise an error on HTTP 4xx/5xx
    raw = response.json()["properties"]["parameter"][parameter]

    # 3) Parse keys like "199001" -> Jan 1990
    records = {}
    for key, value in raw.items():
        year, month = int(key[:4]), int(key[4:])
        if month == 13:          # month 13 = annual average, NOT a real month
            continue
        if value == FILL_VALUE:  # missing data becomes NaN
            value = np.nan
        records[pd.Timestamp(year=year, month=month, day=1)] = value

    series = pd.Series(records, name=parameter).sort_index()
    series.index.name = "date"
    series.to_csv(cache_file)
    return series


def fetch_region(parameter: str, bbox: tuple,
                 start_year: int, end_year: int,
                 n_points: int = 3, pause: float = 0.5):
    """Regional average built from an n_points x n_points grid inside the box.

    Returns (regional_mean_series, DataFrame_of_all_points).
    """
    lat_min, lat_max, lon_min, lon_max = bbox
    lats = np.linspace(lat_min, lat_max, n_points)
    lons = np.linspace(lon_min, lon_max, n_points)

    columns = {}
    for lat in lats:
        for lon in lons:
            columns[(round(lat, 2), round(lon, 2))] = fetch_point(
                parameter, lat, lon, start_year, end_year
            )
            time.sleep(pause)  # be polite to a free public API

    points = pd.DataFrame(columns)
    regional_mean = points.mean(axis=1, skipna=True).rename(parameter)
    regional_mean.index.name = "date"
    return regional_mean, points