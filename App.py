import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Engine Stable", layout="wide")

st.title("VIX Regime Engine – Stable Version (No Crashes)")

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
# SAFE FILTER
# =========================
def active(df, v):
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["VIX", "Qty"])
    return df[df["VIX"] <= v].copy()

# =========================
# SAFE TRADE BUILDER
# =========================
TRADE_COLUMNS = ["Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"]

def build_trades(df, direction):
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=TRADE_COLUMNS)

    trades = []
    for _, row in df.iterrows():
        trades.append({
            "Entry_VIX": row["VIX"],
            "Qty": row["Qty"],
            "Direction": direction,
            "Entry_Price": row["VIX"],
            "Status": "OPEN"
        })

    return pd.DataFrame(trades, columns=TRADE_COLUMNS)

# =========================
# SAFE EXIT LOGIC
# =========================
def apply_exit(trades, current_vix):
    if trades is None or len(trades) == 0:
        return pd.DataFrame(columns=TRADE_COLUMNS)

    trades = trades.copy()

    for i in range(len(trades)):
        if trades.loc[i, "Direction"] == "SHORT":
            if current_vix >= 20:
                trades.loc[i, "Status"] = "CLOSED"

        if trades.loc[i, "Direction"] == "LONG":
            if current_vix < 23:
                trades.loc[i, "Status"] = "CLOSED"

    return trades

# =========================
# ACTIVE LADDERS
# =========================
short_active = active(short_entry, vix)
long_active = active(long_entry, vix)

short_trades = build_trades(short_active, "SHORT")
long_trades = build_trades(long_active, "LONG")

short_trades = apply_exit(short_trades, vix)
long_trades = apply_exit(long_trades, vix)

# =========================
# SAFE SUMS
# =========================
def safe_sum(df, col):
    if df is None or len(df) == 0 or col not in df.columns:
        return 0
    return df[col].sum()

short_qty = safe_sum(short_trades, "Qty")
long_qty = safe_sum(long_trades, "Qty")

# =========================
# EXPOSURE
# =========================
short_notional = short_qty * unit_value
long_notional = long_qty * unit_value

net = long_notional - short_notional

# =========================
# COSTS
# =========================
trade_count = len(short_trades) + len(long_trades)
spread_costs = trade_count * spread

net_pnl = net - spread_costs

# =========================
# RISK CONTROL
# =========================
if abs(net) > max_notional:
    scale = max_notional / abs(net)
    net *= scale

# =========================
# OUTPUT
# =========================
st.subheader("📊 Exposure")

st.write(f"Short Units: {short_qty:.0f}")
st.write(f"Long Units: {long_qty:.0f}")
st.write(f"Net Exposure: {net:.2f} €")

st.subheader("💰 PnL (Stable Model)")

st.write(f"Spread Costs: {spread_costs:.2f} €")
st.write(f"Net PnL (proxy): {net_pnl:.2f} €")

# =========================
# TABLES
# =========================
st.subheader("📉 Short Trades")
st.dataframe(short_trades)

st.subheader("📈 Long Trades")
st.dataframe(long_trades)

# =========================
# STATUS
# =========================
st.subheader("Status")
st.write(regime)
