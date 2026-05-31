import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Portfolio Framework", layout="wide")
st.title("VIX Portfolio Risk Framework")

# =========================
# STATE (PORTFOLIO BUC H)
# =========================
if "positions" not in st.session_state:
    st.session_state.positions = []

if "equity_curve" not in st.session_state:
    st.session_state.equity_curve = [10000]

# =========================
# INPUT
# =========================
vix = st.number_input("VIX", value=18.0)
prev_vix = st.number_input("Prev VIX", value=17.5)
equity = st.number_input("Equity", value=10000)

# =========================
# REGIME
# =========================
def get_regime(v):
    if v < 20:
        return 1
    elif v < 27:
        return 2
    return 3

regime = get_regime(vix)

leverage_map = {1: 10, 2: 6, 3: 3}
max_leverage = leverage_map[regime]

# =========================
# LADDERS
# =========================
short_ladder = pd.DataFrame({
    "level": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
    "qty":   [20, 25, 35, 50, 70, 95, 130, 180, 250]
})

long_ladder = pd.DataFrame({
    "level": [23, 24, 25, 26, 27, 28, 30],
    "qty":   [20, 40, 70, 100, 140, 180, 250]
})

# =========================
# PORTFOLIO CORE
# =========================
def add_position(side, entry, qty):
    st.session_state.positions.append({
        "side": side,
        "entry": entry,
        "qty": qty,
        "status": "OPEN"
    })


def mark_to_market(vix):
    pnl = 0
    exposure = 0

    for p in st.session_state.positions:
        if p["status"] != "OPEN":
            continue

        if p["side"] == "LONG":
            pnl += (vix - p["entry"]) * p["qty"]
            exposure += p["entry"] * p["qty"]
        else:
            pnl += (p["entry"] - vix) * p["qty"]
            exposure -= p["entry"] * p["qty"]

    return pnl, exposure


def close_all_if_regime_shift(old, new):
    if old is None:
        return

    # regime stress reduction
    if new > old:
        for p in st.session_state.positions:
            if p["side"] == "SHORT":
                p["status"] = "CLOSED"

    if new < old:
        for p in st.session_state.positions:
            if p["side"] == "LONG":
                p["status"] = "CLOSED"

# =========================
# SIGNAL ENGINE
# =========================
def crossed(level, prev, current):
    return prev < level <= current


def process_ladder(ladder, side):
    for _, row in ladder.iterrows():
        if crossed(row["level"], prev_vix, vix):
            add_position(side, row["level"], row["qty"])

# =========================
# EXECUTION
# =========================
process_ladder(short_ladder, "SHORT")
process_ladder(long_ladder, "LONG")

# =========================
# REGIME ROTATION
# =========================
if "last_regime" not in st.session_state:
    st.session_state.last_regime = None

close_all_if_regime_shift(st.session_state.last_regime, regime)
st.session_state.last_regime = regime

# =========================
# RISK ENGINE
# =========================
pnl, exposure = mark_to_market(vix)

max_exposure = equity * max_leverage

if abs(exposure) > max_exposure:
    scale = max_exposure / abs(exposure)
    pnl *= scale
    exposure *= scale

equity_now = equity + pnl
st.session_state.equity_curve.append(equity_now)

drawdown = min(st.session_state.equity_curve[-50:]) if len(st.session_state.equity_curve) > 10 else equity_now

# =========================
# OUTPUT
# =========================
st.subheader("Regime")
st.write(regime)

st.subheader("PnL (Unrealized + Realized simplified)")
st.write(pnl)

st.subheader("Exposure")
st.write(exposure)

st.subheader("Equity")
st.write(equity_now)

st.subheader("Drawdown")
st.write(drawdown)

st.subheader("Positions")
st.write(st.session_state.positions)
