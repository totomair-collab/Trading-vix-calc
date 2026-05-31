import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Trade Lifecycle Engine", layout="wide")

st.title("VIX Trade Lifecycle Engine (Real Trades + PnL)")

# =========================
# INPUT
# =========================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)
equity = st.number_input("Kapital (€)", value=10000)

leverage = 10
unit_value = 100
spread = 0.13

max_notional = equity * leverage

# =========================
# REGIME
# =========================
if vix < 20:
    regime = "REGIME 1 (SHORT BUILD)"
elif vix < 23:
    regime = "REGIME 2 (DE-RISK)"
else:
    regime = "REGIME 3 (LONG MODE)"

st.subheader("Regime")
st.info(regime)

# =========================
# ENTRY LADDERS (EDITABLE)
# =========================
st.subheader("📉 Short Entry Ladder")

short_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
        "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic"
)

st.subheader("📈 Long Entry Ladder")

long_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [23, 24, 25, 26, 27, 28, 30],
        "Qty": [20, 40, 70, 100, 140, 180, 250]
    }),
    num_rows="dynamic"
)

# =========================
# EXIT LADDER
# =========================
st.subheader("📤 Short Exit Ladder")

short_exit = st.data_editor(
    pd.DataFrame({
        "VIX": [20, 21, 22, 23],
        "Reduce_%": [0.1, 0.25, 0.5, 1.0]
    }),
    num_rows="dynamic"
)

# =========================
# BUILD ACTIVE EXPOSURE
# =========================
def active(df, v):
    return df[df["VIX"] <= v].copy()

short_active = active(short_entry, vix)
long_active = active(long_entry, vix)

# =========================
# TRADE ENGINE (CORE FIX)
# =========================
# Each ladder step = trade unit

def build_trades(df, direction):
    trades = []
    for _, row in df.iterrows():
        trades.append({
            "Entry_VIX": row["VIX"],
            "Qty": row["Qty"],
            "Direction": direction,
            "Entry_Price": row["VIX"],
            "Status": "OPEN"
        })
    return pd.DataFrame(trades)

short_trades = build_trades(short_active, "SHORT")
long_trades = build_trades(long_active, "LONG")

# =========================
# EXIT LOGIC (REAL CLOSING)
# =========================
def apply_exit(trades, current_vix):
    trades = trades.copy()

    for i in range(len(trades)):
        entry = trades.loc[i, "Entry_VIX"]

        if trades.loc[i, "Direction"] == "SHORT":
            # profit when VIX falls
            if current_vix >= 20:
                trades.loc[i, "Status"] = "CLOSED"

        if trades.loc[i, "Direction"] == "LONG":
            # profit when VIX rises further
            if current_vix < 23:
                trades.loc[i, "Status"] = "CLOSED"

    return trades

short_trades = apply_exit(short_trades, vix)
long_trades = apply_exit(long_trades, vix)

# =========================
# PnL CALCULATION (REALIZED ONLY)
# =========================
def calc_pnl(trades, current_vix):
    pnl = 0
    unrealized = 0

    for _, t in trades.iterrows():
        entry = t["Entry_Price"]
        qty = t["Qty"]

        if t["Direction"] == "SHORT":
            pnl_per = (entry - current_vix)
        else:
            pnl_per = (current_vix - entry)

        trade_pnl = pnl_per * qty * 0.01

        if t["Status"] == "CLOSED":
            pnl += trade_pnl
        else:
            unrealized += trade_pnl

    return pnl, unrealized

short_pnl, short_unreal = calc_pnl(short_trades, vix)
long_pnl, long_unreal = calc_pnl(long_trades, vix)

# =========================
# COSTS
# =========================
total_trades = len(short_trades) + len(long_trades)
spread_costs = total_trades * spread

net_pnl = short_pnl +
