import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plotly.graph_objects as go
import streamlit as st

from src.catalog import REGIONS, VARIABLES
from src.data_loader import fetch_region
from src.forecast import backtest, final_forecast
from src.processing import deseasonalize
from src.trend import mann_kendall, ols_trend

st.set_page_config(page_title="Climate Trend Detective", layout="wide")
st.title("🌍 Climate Trend Detective")
st.caption("Find out whether a NASA climate variable is changing in a region, "
           "by how much, and whether the change is statistically significant.")


@st.cache_data(show_spinner="Fetching NASA POWER data (first run only)...")
def load_series(var, region, start, end):
    series, _ = fetch_region(var, REGIONS[region]["bbox"], start, end)
    return series


# ---------- Sidebar controls (a form avoids re-running on every slider tick) ----------
with st.sidebar.form("controls"):
    var = st.selectbox("Variable", list(VARIABLES),
                       format_func=lambda k: VARIABLES[k]["name"])
    region = st.selectbox("Region", list(REGIONS))
    start, end = st.slider("Years", 1985, 2024, (1990, 2024))
    horizon = st.slider("Forecast horizon (months)", 6, 36, 24)
    submitted = st.form_submit_button("Run analysis")

tab_trend, tab_fc, tab_about = st.tabs(["📈 Trend", "🔮 Forecast", "ℹ️ About"])

with tab_about:
    for k, v in VARIABLES.items():
        st.subheader(f"{v['name']} ({v['units']})")
        st.write(v["definition"])
        st.caption(f"Source: {v['source']}")
    st.subheader("Regions")
    for k, v in REGIONS.items():
        st.write(f"**{k}**: {v['note']}")

if not submitted:
    with tab_trend:
        st.info("Choose a variable and region in the sidebar, then click **Run analysis**.")
    st.stop()

try:
    series = load_series(var, region, start, end)
except Exception as e:
    st.error(f"Could not fetch data from NASA POWER ({e}). Please try again in a minute.")
    st.stop()

if series.isna().all():
    st.error("NASA POWER returned no data for this selection. Try another variable or period.")
    st.stop()

anom = deseasonalize(series)
ols, mkr = ols_trend(anom), mann_kendall(anom)
units, name = VARIABLES[var]["units"], VARIABLES[var]["name"]

# ---------------------------- Trend tab ----------------------------
with tab_trend:
    st.subheader(f"{name} in {region}, {start}-{end}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OLS trend / decade", f"{ols['slope_per_decade']:+.3f} {units}")
    c2.metric("Sen's slope / decade", f"{mkr['sen_slope_per_decade']:+.3f} {units}")
    c3.metric("p (Hamed-Rao MK)", f"{mkr['p_hamed_rao']:.4f}")
    c4.metric("p (OLS, adjusted)", f"{ols['p_adjusted']:.4f}")

    fig = go.Figure()
    fig.add_scatter(x=anom.index, y=anom, mode="lines", name="Anomaly",
                    line=dict(color="lightgray"))
    fig.add_scatter(x=ols["fitted"].index, y=ols["fitted"], name="OLS trend",
                    line=dict(color="crimson", width=3))
    fig.add_scatter(x=mkr["sen_line"].index, y=mkr["sen_line"], name="Sen's slope",
                    line=dict(color="royalblue", width=2, dash="dash"))
    fig.update_layout(yaxis_title=f"Anomaly ({units})", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    significant = mkr["p_hamed_rao"] < 0.05 and ols["p_adjusted"] < 0.05
    direction = mkr["trend"] if mkr["trend"] != "no trend" else "no statistically clear"
    msg = (f"**Result:** {name} shows **{direction}** change of about "
           f"**{ols['slope_per_decade']:+.2f} {units} per decade** "
           f"(95% CI {ols['ci_low_per_decade']:+.2f} to {ols['ci_high_per_decade']:+.2f}).")
    (st.success if significant else st.warning)(
        msg + (" Both tests agree it is statistically significant (p < 0.05)."
               if significant else
               " The evidence is **not** conclusive at the 5% level. A longer record might change that."))

    with st.expander("Why two p-values? What is n_effective?"):
        st.write(f"Monthly anomalies are autocorrelated (lag-1 = {ols['lag1_autocorr']:.2f}), "
                 f"so {ols['n']} months carry the information of only ~{ols['n_effective']:.0f} "
                 f"independent points. Naive p-value: {ols['p_naive']:.2e} (too optimistic). "
                 f"Adjusted: {ols['p_adjusted']:.4f}.")
    with st.expander("Raw series (with seasonal cycle)"):
        st.line_chart(series)

# --------------------------- Forecast tab ---------------------------
with tab_fc:
    with st.spinner("Fitting SARIMA..."):
        bt = backtest(series, horizon=36)
        fc = final_forecast(series, horizon=horizon)

    st.subheader("1. Backtest: can the model be trusted?")
    b1, b2, b3 = st.columns(3)
    b1.metric("SARIMA MAE", f"{bt['mae_sarima']:.3f} {units}")
    b2.metric("Baseline MAE", f"{bt['mae_naive']:.3f} {units}")
    b3.metric("Skill vs baseline", f"{bt['skill']*100:+.1f}%")

    f1 = go.Figure()
    f1.add_scatter(x=bt["actual"].index, y=bt["actual"], name="Actual", line=dict(color="black"))
    f1.add_scatter(x=bt["sarima"].index, y=bt["sarima"], name="SARIMA", line=dict(color="crimson"))
    f1.add_scatter(x=bt["naive"].index, y=bt["naive"], name="Seasonal naive",
                   line=dict(color="gray", dash="dot"))
    st.plotly_chart(f1, use_container_width=True)
    if bt["skill"] <= 0:
        st.info("SARIMA did not beat the 'same as last year' baseline here, "
                "which is common for strongly seasonal climate data.")

    st.subheader(f"2. Forecast: next {horizon} months")
    hist = series.iloc[-120:]
    f2 = go.Figure()
    f2.add_scatter(x=hist.index, y=hist, name="History", line=dict(color="black"))
    f2.add_scatter(x=fc.index, y=fc["upper"], line=dict(width=0), showlegend=False)
    f2.add_scatter(x=fc.index, y=fc["lower"], fill="tonexty", name="95% interval",
                   line=dict(width=0), fillcolor="rgba(220,20,60,0.2)")
    f2.add_scatter(x=fc.index, y=fc["forecast"], name="Forecast", line=dict(color="crimson"))
    f2.update_layout(yaxis_title=units)
    st.plotly_chart(f2, use_container_width=True)