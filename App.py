import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Event Engine", layout="wide")

st.title("VIX Event-Driven Trading Engine")

# =========================
# SESSION STATE INIT
# =========================
if "short_trades" not in st.session_state:
    st.session_state.short_trades = pd.DataFrame(columns=[
        "TradeID", "Entry_VIX", "Qty", "Direction", "Status"
    ])

if "long_trades" not in st.session_state:
    st.session_state.long_trades = pd.DataFrame(columns=[
        "TradeID", "Entry_VIX", "Qty", "Direction", "Status"
    ])

if "last_vix" not in st.session_state:
    st.session_state.last_vix = None

# =========================
# INPUT
# =========================
vix = st.number_input("Current VIX", value=18.0)
prev_vix = st.number_input("Previous VIX", value=17.5)
equity = st.number_input("Capital (€)", value=10000)

unit_value = 100
spread = 0.13
max_notional = equity * 10

# store last
st.session_state.last_vix = prev_vix

# =========================
# LADDER INPUTS (EDITABLE)
# =========================
st.subheader("📉 Short Ladder")

short_ladder = st.data_editor(
    pd.DataFrame({
        "Level": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
        "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic"
)

st.subheader("📈 Long Ladder")

long_ladder = st.data_editor(
    pd.DataFrame({
        "Level": [23, 24, 25, 26, 27, 28, 30],
        "Qty": [20, 40, 70, 100, 140, 180, 250]
    }),
    num_rows="dynamic"
)

# =========================
# EVENT DETECTION
# =========================
def crossed_up(level, prev, current):
    return prev < level <= current

def crossed_down(level, prev, current):
    return prev > level >= current

# =========================
# CREATE TRADES (ONLY ON EVENTS)
# =========================
def add_trade(store, level, qty, direction):
    trade_id = f"{direction}_{level}"

    if trade_id in store["TradeID"].values:
        return store  # already exists

    new_trade = pd.DataFrame([{
        "TradeID": trade_id,
        "Entry_VIX": level,
        "Qty": qty,
        "Direction": direction,
        "Status": "OPEN"
    }])

    return pd.concat([store, new_trade], ignore_index=True)

# =========================
# APPLY EVENTS
# =========================
for _, row in short_ladder.iterrows():
    if crossed_up(row["Level"], prev_vix, vix):
        st.session_state.short_trades = add_trade(
            st.session_state.short_trades,
            row["Level"],
            row["Qty"],
            "SHORT"
        )

for _, row in long_ladder.iterrows():
    if crossed_up(row["Level"], prev_vix, vix):
        st.session_state.long_trades = add_trade(
            st.session_state.long_trades,
            row["Level"],
            row["Qty"],
            "LONG"
        )

# =========================
# SIMPLE EXIT MODEL (REGIME-BASED)
# =========================
if vix >= 20:
    st.session_state.short_trades.loc[
        st.session_state.short_trades["Direction"] == "SHORT",
        "Status"
    ] = "CLOSED"

if vix < 23:
    st.session_state.long_trades.loc[
        st.session_state.long_trades["Direction"] == "LONG",
        "Status"
    ] = "CLOSED"

# =========================
# EXPOSURE
# =========================
def open_qty(df):
    if df is None or len(df) == 0:
        return 0
    return df[df["Status"] == "OPEN"]["Qty"].sum()

short_qty = open_qty(st.session_state.short_trades)
long_qty = open_qty(st.session_state.long_trades)

short_notional = short_qty * unit_value
long_notional = long_qty * unit_value

net = long_notional - short_notional

# =========================
# COSTS
# =========================
total_trades = len(st.session_state.short_trades) + len(st.session_state.long_trades)
spread_costs = total_trades * spread

# =========================
# PnL (REALIZED ONLY)
# =========================
def pnl(df):
    if df is None or len(df) == 0:
        return 0

    total = 0

    for _, t in df.iterrows():
        if t["Status"] != "CLOSED":
            continue

        entry = t["Entry_VIX"]
        qty = t["Qty"]

        if t["Direction"] == "SHORT":
            total += (entry - vix) * qty * 0.01
        else:
            total += (vix - entry) * qty * 0.01

    return total

net_pnl = pnl(st.session_state.short_trades) + pnl(st.session_state.long_trades
