"""Forecasting with SARIMA, honestly evaluated against a seasonal-naive baseline."""

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")

ORDER = (1, 1, 1)
SEASONAL_ORDER = (1, 1, 1, 12)


def prepare(series: pd.Series) -> pd.Series:
    """Force a regular monthly index and fill tiny gaps."""
    return series.asfreq("MS").interpolate(limit_direction="both")


def _fit(train: pd.Series):
    model = SARIMAX(
        train, order=ORDER, seasonal_order=SEASONAL_ORDER,
        enforce_stationarity=False, enforce_invertibility=False,
    )
    return model.fit(disp=False)


def backtest(series: pd.Series, horizon: int = 36) -> dict:
    """Hold out the LAST `horizon` months, forecast them, compare to the baseline."""
    s = prepare(series)
    train, test = s.iloc[:-horizon], s.iloc[-horizon:]

    pred = _fit(train).get_forecast(horizon).predicted_mean.to_numpy()
    # Seasonal naive: "next year looks like the last observed year"
    naive = np.tile(train.to_numpy()[-12:], int(np.ceil(horizon / 12)))[:horizon]
    actual = test.to_numpy()

    def mae(p): return float(np.mean(np.abs(actual - p)))
    def rmse(p): return float(np.sqrt(np.mean((actual - p) ** 2)))

    return {
        "actual": test,
        "sarima": pd.Series(pred, index=test.index),
        "naive": pd.Series(naive, index=test.index),
        "mae_sarima": mae(pred), "mae_naive": mae(naive),
        "rmse_sarima": rmse(pred), "rmse_naive": rmse(naive),
        "skill": 1 - mae(pred) / mae(naive),   # >0 means SARIMA beats the baseline
    }


def final_forecast(series: pd.Series, horizon: int = 24) -> pd.DataFrame:
    """Refit on ALL data and forecast the future with a 95% interval."""
    s = prepare(series)
    fc = _fit(s).get_forecast(horizon)
    ci = fc.conf_int(alpha=0.05)
    return pd.DataFrame({
        "forecast": fc.predicted_mean,
        "lower": ci.iloc[:, 0],
        "upper": ci.iloc[:, 1],
    })