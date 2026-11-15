"""Preprocessing: turn a raw monthly series into deseasonalized anomalies."""

import pandas as pd


def deseasonalize(series: pd.Series) -> pd.Series:
    """Subtract each calendar month's long-term mean (the 'climatology').

    Example: every January value has the average of all Januaries removed.
    What remains is the *anomaly*: how unusual that month was for its season.
    """
    climatology = series.groupby(series.index.month).transform("mean")
    anomalies = series - climatology
    anomalies.name = f"{series.name}_anomaly"
    return anomalies