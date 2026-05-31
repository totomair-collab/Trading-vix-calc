import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Engine", layout="wide")
st.title("VIX Event Engine (Crash Safe)")

# =========================
# STATE
# =========================
if "short_trades" not in st.session_state:
    st.session_state.short_trades = pd.DataFrame(columns=[
        "TradeID", "Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"
    ])

if "long_trades" not in st.session_state:
    st.session_state.long_trades = pd.DataFrame(columns=[
        "TradeID", "Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"
    ])

# =========================
# INPUT
# =========================
vix = st.number_input("Current VIX", value=18.0)
prev_vix = st.number_input("Previous VIX", value=17.5)
equity = st.number_input("Capital", value=10000)

unit_value = 100
spread = 0.13
max_notional = equity * 10

# =========================
# LADDERS
# =========================
short_ladder = st.data_editor(pd.DataFrame({
    "Level": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
    "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
}), num_rows="dynamic")

long_ladder = st.data_editor(pd.DataFrame({
    "Level": [23, 24, 25, 26, 27, 28, 30],
    "Qty": [20, 40, 70, 100, 140, 180, 250]
}), num_rows="dynamic")

# =========================
# FUNCTIONS
# =========================
def crossed(level, prev, current):
    return prev < level <= current


def add_trade(store, level, qty, direction):
    trade_id = direction + "_" + str(level)

    if trade_id in store["TradeID"].values:
        return store

    new_row = pd.DataFrame([{
        "TradeID": trade_id,
        "Entry_VIX": level,
        "Qty": qty,
        "Direction": direction,
        "Entry_Price": level,
        "Status": "OPEN"
    }])

    return pd.concat([store, new_row], ignore_index=True)


def apply_events_loop(ladder, prev, current, direction, store):
    if ladder is None or len(ladder) == 0:
        return store

    for i in range(len(ladder)):
        level = ladder.iloc[i]["Level"]
        qty = ladder.iloc[i]["Qty"]

        if crossed(level, prev, current):
            store = add_trade(store, level, qty, direction)

    return store


def apply_exit(df, vix):
    if df is None or len(df) == 0:
        return df

    df = df.copy()

    for i in range(len(df)):
        if df.loc[i, "Direction"] == "SHORT" and vix >= 20:
            df.loc[i, "Status"] = "CLOSED"

        if df.loc[i, "Direction"] == "LONG" and vix < 23:
            df.loc[i, "Status"] = "CLOSED"

    return df


def open_qty(df):
    if df is None or len(df) == 0:
        return 0
    return df[df["Status"] == "OPEN"]["Qty"].sum()


def pnl(df, vix):
    if df is None or len(df) == 0:
        return 0

    total = 0

    for _, t in df.iterrows():
        if t["Status"] != "CLOSED":
            continue

        entry = t["Entry_Price"]
        qty = t["Qty"]

        if t["Direction"] == "SHORT":
            total += (entry - vix) * qty * 0.01
        else:
            total += (vix - entry) * qty * 0.01

    return total

# =========================
# EXECUTION (NO BROKEN BRACKETS)
# =========================

tmp_short = apply_events_loop(short_ladder, prev_vix, vix, "SHORT", st.session_state.short_trades)
st.session_state.short_trades = tmp_short

tmp_long = apply_events_loop(long_ladder, prev_vix, vix, "LONG", st.session_state.long_trades)
st.session_state.long_trades = tmp_long

st.session_state.short_trades = apply_exit(st.session_state.short_trades, vix)
st.session_state.long_trades = apply_exit(st.session_state.long_trades, vix)

# =========================
# METRICS
# =========================
short_qty = open_qty(st.session_state.short_trades)
long_qty = open_qty(st.session_state.long_trades)

net_exposure = (long_qty - short_qty) * unit_value

spread_costs = (
    len(st.session_state.short_trades)
    + len(st.session_state.long_trades)
) * spread

net_pnl = pnl(st.session_state.short_trades, vix) + pnl(st.session_state.long_trades, vix) - spread_costs

# =========================
# RISK CAP
# =========================
max_notional = equity * 10

if abs(net_exposure) > max_notional:
    net_exposure = max_notional * (1 if net_exposure > 0 else -1)

# =========================
# OUTPUT
# =========================
st.subheader("Exposure")
st.write(net_exposure)

st.subheader("PnL")
st.write(net_pnl)
st.write(spread_costs)

st.subheader("Trades Short")
st.dataframe(st.session_state.short_trades)

st.subheader("Trades Long")
st.dataframe(st.session_state.long_trades)
