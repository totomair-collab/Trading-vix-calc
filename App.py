import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="VIX Institutional Research Engine", layout="wide")
st.title("VIX Institutional Risk & Research Framework")

# =========================
# INPUT DATA
# =========================
vix_series = st.data_editor(
    pd.DataFrame({
        "Day": list(range(1, 61)),
        "VIX": np.clip(np.linspace(16, 28, 60) + np.random.normal(0, 0.7, 60), 10, 40)
    }),
    num_rows="dynamic"
)

initial_equity = st.number_input("Initial Capital", value=10000)

# =========================
# REGIME MODEL
# =========================
def regime(v):
    if v < 20:
        return 1   # low vol
    elif v < 27:
        return 2   # normal stress
    return 3       # crisis

# Capital allocation per regime (IMPORTANT)
risk_budget_map = {
    1: 0.50,   # calm markets → moderate allocation
    2: 0.80,   # active regime → higher allocation
    3: 0.40    # crisis → risk reduction (deleveraging)
}

# =========================
# STRATEGY PARAMETERS (OPTIMIZABLE)
# =========================
short_levels = [17.25, 17.5, 18.0, 18.5, 19.0]
long_levels  = [23, 24, 25, 26, 27]

base_short_qty = st.slider("Short Base Risk", 10, 100, 30)
base_long_qty  = st.slider("Long Base Risk", 10, 100, 40)

# =========================
# CORE BACKTEST ENGINE
# =========================
def run_engine(data):
    equity = initial_equity
    prev = None
    positions = []

    equity_curve = []

    for _, row in data.iterrows():
        v = row["VIX"]
        reg = regime(v)

        risk_budget = risk_budget_map[reg]

        # SCALE POSITION SIZING BY RISK BUDGET
        short_qty = base_short_qty * risk_budget
        long_qty  = base_long_qty * risk_budget

        if prev is not None:

            # ENTRY LOGIC
            for l in short_levels:
                if prev < l <= v:
                    positions.append(("SHORT", l, short_qty, reg))

            for l in long_levels:
                if prev < l <= v:
                    positions.append(("LONG", l, long_qty, reg))

        # MARK-TO-MARKET
        pnl = 0
        for side, entry, qty, r in positions:
            if side == "LONG":
                pnl += (v - entry) * qty
            else:
                pnl += (entry - v) * qty

        equity_curve.append(equity + pnl)

        prev = v

    return equity_curve, positions

# =========================
# WALK-FORWARD VALIDATION
# =========================
n = len(vix_series)
split = max(10, n // 3)

segments = [
    vix_series.iloc[:split],
    vix_series.iloc[split:2*split],
    vix_series.iloc[2*split:]
]

segment_results = []
segment_volatility = []

for seg in segments:
    if len(seg) < 5:
        continue

    curve, pos = run_engine(seg)

    returns = np.diff(curve)
    total_return = curve[-1] - curve[0]
    vol = np.std(returns) if len(returns) > 1 else 0

    segment_results.append(total_return)
    segment_volatility.append(vol)

# =========================
# PERFORMANCE METRICS
# =========================
avg_return = np.mean(segment_results)
std_return = np.std(segment_results)

# robustness (institutional style)
robustness = avg_return / (std_return + 1e-9)

# overfitting penalty (VERY IMPORTANT)
overfit_penalty = std_return * 0.5 + np.max(np.abs(segment_results)) * 0.2

final_score = avg_return - overfit_penalty

# =========================
# REGIME DISTRIBUTION
# =========================
regimes = vix_series["VIX"].apply(regime)
reg_dist = regimes.value_counts(normalize=True)

# =========================
# OUTPUT
# =========================
st.subheader("Institutional Performance")

st.write("Average Return (Walk-Forward):", avg_return)
st.write("Volatility of Returns:", std_return)
st.write("Robustness Score:", robustness)
st.write("Overfitting Penalty:", overfit_penalty)
st.write("Final Score (Risk-Adjusted):", final_score)

st.subheader("Regime Distribution")
st.write(reg_dist)

st.subheader("Segment Results")
st.write(segment_results)

st.subheader("Segment Volatility")
st.write(segment_volatility)
