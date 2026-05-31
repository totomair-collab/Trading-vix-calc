import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Backtest Engine", layout="wide")
st.title("VIX Quant Backtest Framework")

# =========================
# STATE
# =========================
if "trades" not in st.session_state:
    st.session_state.trades = []

if "equity_curve" not in st.session_state:
    st.session_state.equity_curve = []

# =========================
# INPUT: SIMULATED SERIES
# =========================
st.subheader("VIX Time Series (Backtest Input)")

vix_data = st.data_editor(
    pd.DataFrame({
        "VIX": [17.2, 17.5, 17.8, 18.2, 18.6, 19.1, 19.6, 20.2, 21.5, 23.0, 25.0]
    }),
    num_rows="dynamic"
)

equity = st.number_input("Initial Equity", value=10000)

# =========================
# REGIME
# =========================
def regime(v):
    if v < 20:
        return 1
    elif v < 27:
        return 2
    return 3

leverage_map = {1: 10, 2: 6, 3: 3}

# =========================
# LADDER (FIXED STRATEGY MODEL)
# =========================
short_levels = [(17.25, 20), (17.5, 35), (18.0, 50), (18.5, 80), (19.0, 120)]
long_levels  = [(23.0, 30), (24.0, 60), (25.0, 100), (26.0, 140)]

# =========================
# BACKTEST ENGINE
# =========================
positions = []
equity_curve = [equity]

def add_trade(side, entry, qty):
    positions.append({
        "side": side,
        "entry": entry,
        "qty": qty,
        "status": "OPEN"
    })

def close_by_regime(old, new):
    if old is None:
        return

    if new > old:
        for p in positions:
            if p["side"] == "SHORT":
                p["status"] = "CLOSED"

    if new < old:
        for p in positions:
            if p["side"] == "LONG":
                p["status"] = "CLOSED"

def pnl(vix):
    total = 0
    for p in positions:
        if p["status"] != "CLOSED":
            continue

        if p["side"] == "LONG":
            total += (vix - p["entry"]) * p["qty"]
        else:
            total += (p["entry"] - vix) * p["qty"]
    return total

# =========================
# SIMULATION LOOP
# =========================
prev_vix = None
last_regime = None

for i, row in vix_data.iterrows():
    vix = row["VIX"]
    reg = regime(vix)

    if prev_vix is not None:

        # signals
        for lvl, qty in short_levels:
            if prev_vix < lvl <= vix:
                add_trade("SHORT", lvl, qty)

        for lvl, qty in long_levels:
            if prev_vix < lvl <= vix:
                add_trade("LONG", lvl, qty)

        # regime change logic
        close_by_regime(last_regime, reg)

    # valuation
    current_pnl = pnl(vix)
    equity_curve.append(equity + current_pnl)

    prev_vix = vix
    last_regime = reg

# =========================
# METRICS
# =========================
final_equity = equity_curve[-1]
max_dd = min(equity_curve)

trades_df = pd.DataFrame(positions)

# =========================
# OUTPUT
# =========================
st.subheader("Final Equity")
st.write(final_equity)

st.subheader("Max Drawdown (raw)")
st.write(max_dd)

st.subheader("Equity Curve")
st.write(equity_curve)

st.subheader("Trades")
st.dataframe(trades_df)
