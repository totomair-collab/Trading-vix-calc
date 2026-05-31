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
                p["status"] = "C
