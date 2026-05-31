import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Stable Trading System", layout="wide")
st.title("VIX Stable Portfolio + Order Journal")

# =========================
# STATE
# =========================
if "orders" not in st.session_state:
    st.session_state.orders = []

if "positions" not in st.session_state:
    st.session_state.positions = []

if "equity_curve" not in st.session_state:
    st.session_state.equity_curve = [10000]

if "last_regime" not in st.session_state:
    st.session_state.last_regime = None

# =========================
# INPUT
# =========================
vix = st.number_input("Current VIX", value=18.0)
prev_vix = st.number_input("Previous VIX", value=17.5)
equity = st.number_input("Starting Equity", value=10000)

# =========================
# REGIME ENGINE
# =========================
def get_regime(v):
    if v < 20:
        return 1
    elif v < 27:
        return 2
    return 3

regime = get_regime(vix)

leverage_map = {
    1: 10,
    2: 6,
    3: 3
}

max_leverage = leverage_map[regime]
max_exposure = equity * max_leverage

# =========================
# ENTRY TABLES (EDITABLE)
# =========================
st.subheader("Short Entry Ladder")

short_ladder = st.data_editor(
    pd.DataFrame({
        "Level": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
        "Qty":   [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic",
    key="short_table"
)

st.subheader("Long Entry Ladder")

long_ladder = st.data_editor(
    pd.DataFrame({
        "Level": [23, 24, 25, 26, 27, 28, 30],
        "Qty":   [20, 40, 70, 100, 140, 180, 250]
    }),
    num_rows="dynamic",
    key="long_table"
)

# =========================
# HELPERS
# =========================
def crossed(level, prev, current):
    return prev < level <= current


def add_order(side, level, qty, status):
    st.session_state.orders.append({
        "side": side,
        "level": level,
        "qty": qty,
        "status": status
    })


def add_position(side, level, qty):
    st.session_state.positions.append({
        "side": side,
        "entry": level,
        "qty": qty,
        "status": "OPEN"
    })


# =========================
# SIGNAL ENGINE
# =========================
def process_ladder(ladder, side):
    for _, r in ladder.iterrows():
        if crossed(r["Level"], prev_vix, vix):
            add_position(side, r["Level"], r["Qty"])
            add_order(side, r["Level"], r["Qty"], "FILLED")


# =========================
# POSITION ENGINE
# =========================
def mark_to_market():
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


# =========================
# REGIME ROTATION
# =========================
def rotate(old, new):
    if old is None:
        return

    # risk reduction in stress increase
    if new > old:
        for p in st.session_state.positions:
            if p["side"] == "SHORT":
                p["status"] = "CLOSED"

    if new < old:
        for p in st.session_state.positions:
            if p["side"] == "LONG":
                p["status"] = "CLOSED"


# =========================
# EXECUTION
# =========================
process_ladder(short_ladder, "SHORT")
process_ladder(long_ladder, "LONG")

rotate(st.session_state.last_regime, regime)
st.session_state.last_regime = regime

# =========================
# RISK ENGINE
# =========================
pnl, exposure = mark_to_market()

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

st.subheader("PnL")
st.write(pnl)

st.subheader("Exposure")
st.write(exposure)

st.subheader("Equity Curve")
st.write(equity_now)

st.subheader("Drawdown")
st.write(drawdown)

st.subheader("Order Journal")
st.dataframe(pd.DataFrame(st.session_state.orders))

st.subheader("Positions")
st.dataframe(pd.DataFrame(st.session_state.positions))
