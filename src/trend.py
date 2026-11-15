"""Linear trend estimation and significance testing."""

import numpy as np
import pandas as pd
import pymannkendall as mk
from scipy import stats


def to_years(index: pd.DatetimeIndex) -> np.ndarray:
    """Decimal years, e.g. July 2000 -> 2000.5 (so the slope is per YEAR)."""
    return (index.year + (index.month - 1) / 12).to_numpy()


def ols_trend(series: pd.Series, alpha: float = 0.05) -> dict:
    """OLS slope with a naive p-value AND an autocorrelation-adjusted one."""
    s = series.dropna()
    x, y = to_years(s.index), s.to_numpy()
    n = len(y)

    fit = stats.linregress(x, y)  # slope, intercept, rvalue, pvalue, stderr
    fitted = fit.intercept + fit.slope * x
    resid = y - fitted

    # Effective sample size from lag-1 autocorrelation of residuals
    r1 = np.corrcoef(resid[:-1], resid[1:])[0, 1]
    n_eff = n * (1 - r1) / (1 + r1) if r1 > 0 else n
    n_eff = float(np.clip(n_eff, 4, n))

    se_adj = fit.stderr * np.sqrt((n - 2) / (n_eff - 2))
    df_adj = n_eff - 2
    t_stat = fit.slope / se_adj
    p_adj = 2 * stats.t.sf(abs(t_stat), df_adj)
    t_crit = stats.t.ppf(1 - alpha / 2, df_adj)

    return {
        "slope_per_decade": fit.slope * 10,
        "ci_low_per_decade": (fit.slope - t_crit * se_adj) * 10,
        "ci_high_per_decade": (fit.slope + t_crit * se_adj) * 10,
        "p_naive": fit.pvalue,
        "p_adjusted": p_adj,
        "r_squared": fit.rvalue ** 2,
        "lag1_autocorr": r1,
        "n": n,
        "n_effective": n_eff,
        "fitted": pd.Series(fitted, index=s.index),
    }


def mann_kendall(series: pd.Series) -> dict:
    """Mann-Kendall (plain + Hamed-Rao autocorrelation-corrected) and Sen's slope."""
    s = series.dropna()
    y = s.to_numpy()

    plain = mk.original_test(y)
    corrected = mk.hamed_rao_modification_test(y)

    # pymannkendall's slope is per time step (per month) -> x120 = per decade
    sen_slope_month = plain.slope
    sen_line = plain.intercept + sen_slope_month * np.arange(len(y))

    return {
        "trend": corrected.trend,           # 'increasing' / 'decreasing' / 'no trend'
        "tau": plain.Tau,
        "p_plain": plain.p,
        "p_hamed_rao": corrected.p,
        "sen_slope_per_decade": sen_slope_month * 120,
        "sen_line": pd.Series(sen_line, index=s.index),
    }