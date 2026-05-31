import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Session Dynamics Engine", layout="wide")

st.title("VIX Session Dynamics Engine")

# =========================
# SESSION STATE INIT
# =========================
if "short_trades" not in st.session_state:
    st.session_state.short_trades = pd.DataFrame(columns=["Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"])

if "long_trades" not in st.session_state:
    st.session_state.long_trades = pd.DataFrame(columns=["Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"])

# =========================
# INPUTS
# =========================
st.subheader("📊 Session Inputs")

start_vix = st.number_input("Session Start VIX", value=17.5)
current_vix = st.number_input("Current VIX", value=18.5)
hours_elapsed = st.number_input("Hours since start", value=1.0)

equity = st.number_input("Capital (€)", value=10000)

leverage = 10
unit_value = 100
spread = 0.13

max_notional = equity * leverage

# =========================
# VIX DYNAMICS
# =========================
vix_delta = current_vix - start_vix
vix_speed = vix_delta / max(hours_elapsed, 0.1)

st.subheader("⚡ Market Dynamics")

st.write(f"VIX Change: {vix_delta:.2f}")
st.write(f"VIX Speed (per hour): {vix_speed:.2f}")

# =========================
# DYNAMIC REGIME
# =========================
if current_vix < 20:
    regime = "REGIME 1 (SHORT BUILD)"
elif current_vix < 23:
    regime = "REGIME 2 (DE-RISK)"
else:
    regime = "REGIME 3 (LONG MODE)"

# adjust regime pressure via speed
if vix_speed > 1.0:
    regime = regime + " + HIGH STRESS"

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
# SAFE ACTIVE FILTER
# =========================
def active(df, v):
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["VIX", "Qty"])
    return df[df["VIX"] <= v].copy()

# =========================
# BUILD TRADES (PERSISTENT)
# =========================
TRADE_COLUMNS = ["Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"]

def build_trades(df, direction):
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=TRADE_COLUMNS)

    trades = []
    for _, r in df.iterrows():
        trades.append({
            "Entry_VIX": r["VIX"],
            "Qty": r["Qty"],
            "Direction": direction,
            "Entry_Price": r["VIX"],
            "Status": "OPEN"
        })

    return pd.DataFrame(trades, columns=TRADE_COLUMNS)

# =========================
# EXIT LOGIC (SESSION BASED)
# =========================
def apply_exit(trades, vix, speed):
    if trades is None or len(trades) == 0:
        return trades

    trades = trades.copy()

    for i in range(len(trades)):
        if trades.loc[i, "Direction"] == "SHORT":
            if vix >= 20 or speed > 1.2:
                trades.loc[i, "Status"] = "CLOSED"

        if trades.loc[i, "Direction"] == "LONG":
            if vix < 23 and speed < 0:
                trades.loc[i, "Status"] = "CLOSED"

    return trades

# =========================
# ACTIVE LADDERS
# =========================
short_active = active(short_entry, current_vix)
long_active = active(long_entry, current_vix)

new_short = build_trades(short_active, "SHORT")
new_long = build_trades(long_active, "LONG")

# merge into session (persisting behavior)
st.session_state.short_trades = pd.concat([st.session_state.short_trades, new_short], ignore_index=True)
st.session_state.long_trades = pd.concat([st.session_state.long_trades, new_long], ignore_index=True)

# apply exit
st.session_state.short_trades = apply_exit(st.session_state.short_trades, current_vix, vix_speed)
st.session_state.long_trades = apply_exit(st.session_state.long_trades, current_vix, vix_speed)

# =========================
# SAFE SUM
# =========================
def safe_sum(df, col):
    if df is None or len(df) == 0 or col not in df.columns:
        return 0
    return df[df["Status"] == "OPEN"][col].sum()

short_qty = safe_sum(st.session_state.short_trades, "Qty")
long_qty = safe_sum(st.session_state.long_trades, "Qty")

# =========================
# EXPOSURE
# =========================
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
def calc_pnl(df, vix):
    pnl = 0

    if df is None or len(df) == 0:
        return 0

    for _, t in df.iterrows():
        entry = t["Entry_Price"]
        qty = t["Qty"]

        if t["Status"] == "CLOSED":
            if t["Direction"] == "SHORT":
                pnl += (entry - vix) * qty * 0.01
            else:
                pnl += (vix - entry) * qty * 0.01

    return pnl

short_pnl = calc_pnl(st.session_state.short_trades, current_vix)
long_pnl = calc_pnl(st.session_state.long_trades, current_vix)

net_pnl = short_pnl + long_pnl - spread_costs

# =========================
# OUTPUT
# =========================
st.subheader("📊 Exposure")

st.write(f"Short Open Units: {short_qty:.0f}")
st.write(f"Long Open Units: {long_qty:.0f}")
st.write(f"Net Exposure: {net:.2f} €")

st.subheader("💰 PnL (Session Model)")

st.write(f"Short PnL (realized): {short_pnl:.2f} €")
st.write(f"Long PnL (realized): {long_pnl:.2f} €")
st.write(f"Spread Costs: {spread_costs:.2f} €")
st.write(f"Net PnL: {net_pnl:.2f} €")

# =========================
# TABLES
# =========================
st.subheader("📉 Short Trades (Session)")
st.dataframe(st.session_state.short_trades)

st.subheader("📈 Long Trades (Session)")
st.dataframe(st.session_state.long_trades)

# =========================
# STATUS
# =========================
st.subheader("Status")
st.write(regime)
