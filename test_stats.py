import numpy as np
import pandas as pd

from src.processing import deseasonalize
from src.trend import ols_trend, mann_kendall

rng = np.random.default_rng(42)
idx = pd.date_range("1990-01-01", periods=420, freq="MS")
t_years = np.arange(420) / 12
month = idx.month.to_numpy()

season = 10 * np.sin(2 * np.pi * (month - 1) / 12)
noise = np.zeros(420)
for i in range(1, 420):                      # AR(1) noise, rho = 0.5
    noise[i] = 0.5 * noise[i - 1] + rng.normal(0, 0.5)

y = pd.Series(20 + 0.03 * t_years + season + noise, index=idx, name="synthetic")
# TRUE trend = 0.03 per year = 0.30 per decade

anom = deseasonalize(y)
o = ols_trend(anom)
m = mann_kendall(anom)

print(f"True slope           : 0.300 per decade")
print(f"OLS slope            : {o['slope_per_decade']:.3f}  "
      f"CI [{o['ci_low_per_decade']:.3f}, {o['ci_high_per_decade']:.3f}]")
print(f"Sen's slope          : {m['sen_slope_per_decade']:.3f}")
print(f"p naive / adjusted   : {o['p_naive']:.2e} / {o['p_adjusted']:.2e}")
print(f"n / n_effective      : {o['n']} / {o['n_effective']:.0f}")
print(f"Mann-Kendall verdict : {m['trend']}")