import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="VIX Regime Engine ADV", layout="wide")

st.title("VIX Regime Engine – Advanced Risk + PnL + Stress")

# =========================
# INPUT
# =========================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)
equity = st.number_input("Kapital (€)", value=10000)

leverage = 10
unit_value = 100
spread = 0.13

max_notional = equity * leverage

# simulated last VIX for velocity
prev_vix = st.number_input("VIX vorheriger Wert (für Velocity)", value=17.5)

vix_velocity = vix - prev_vix

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
# LADDERS (EDITABLE)
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

st.subheader("📤 Short Exit Ladder")

short_exit = st.data_editor(
    pd.DataFrame({
        "VIX": [20, 21, 22, 23],
        "Reduce_%": [0.1, 0.25, 0.5, 1.0]
    }),
    num_rows="dynamic"
)

# =========================
# HELPERS
# =========================
def build(df):
    df = df.copy()
    df["Notional"] = df["Qty"] * unit_value
    df["Accumulated_Qty"] = df["Qty"].cumsum()
    df["Accumulated_Notional"] = df["Notional"].cumsum()
    return df

def active(df, v):
    return df[df["VIX"] <= v]

def exit_reduction(df, v):
    rows = df[df["VIX"] <= v]
    if len(rows) == 0:
        return 0
    return rows["Reduce_%"].iloc[-1]

# =========================
# TABLES
# =========================
short_table = build(short_entry)
long_table = build(long_entry)

short_active = active(short_table, vix)
long_active = active(long_table, vix)

short_qty = short_active["Qty"].sum()
long_qty = long_active["Qty"].sum()

# =========================
# REGIME LOGIC
# =========================
if regime == "REGIME 1 (SHORT BUILD)":
    short_pos = short_qty
    long_pos = 0

elif regime == "REGIME 2 (DE-RISK)":
    short_pos = short_qty * (1 - exit_reduction(short_exit, vix))
    long_pos = 0

else:
    short_pos = 0
    long_pos = long_qty

# =========================
# COSTS
# =========================
spread_costs = (short_pos + long_pos) * spread

# =========================
# EXPOSURE
# =========================
short_notional = short_pos * unit_value
long_notional = long_pos * unit_value

net = long_notional - short_notional - spread_costs

# =========================
# MARGIN CONTROL
# =========================
if abs(net) > max_notional:
    scale = max_notional / abs(net)
    short_notional *= scale
    long_notional *= scale
    net *= scale

# =========================
# PnL MODEL (SIMPLIFIED)
# =========================
# assumption: 1 VIX point move = 1% effect proxy
pnl_short = short_notional * (19 - vix) * 0.01
pnl_long = long_notional * (vix - 23) * 0.01

pnl_total = pnl_short + pnl_long - spread_costs

# =========================
# BREAK-EVEN
# =========================
if short_notional > 0:
    breakeven_short = 19  # anchor (simplified model)
else:
    breakeven_short = None

if long_notional > 0:
    breakeven_long = 23
else:
    breakeven_long = None

# =========================
# VIX VELOCITY (CRASH DETECTOR)
# =========================
st.subheader("⚡ VIX Velocity")

st.write(f"VIX Change: {vix_velocity:.2f}")

if vix_velocity > 1.5:
    st.error("⚠️ VOLMAGEDDON WARNING – Spike detected")
elif vix_velocity > 0.8:
    st.warning("High volatility expansion")
else:
    st.success("Normal volatility regime")

# =========================
# OUTPUT
# =========================
st.subheader("📊 Exposure")

st.write(f"Short Units: {short_pos:.0f}")
st.write(f"Long Units: {long_pos:.0f}")
st.write(f"Net Exposure: {net:.2f} €")

st.subheader("💰 PnL Simulation")

st.write(f"PnL Short: {pnl_short:.2f} €")
st.write(f"PnL Long: {pnl_long:.2f} €")
st.write(f"Spread Costs: {spread_costs:.2f} €")
st.write(f"Total PnL: {pnl_total:.2f} €")

st.subheader("🎯 Break-even")

st.write(f"Short BE: {breakeven_short}")
st.write(f"Long BE: {breakeven_long}")

# =========================
# TABLE OUTPUT
# =========================
st.subheader("📉 Short Ladder")
st.dataframe(short_table)

st.subheader("📈 Long Ladder")
st.dataframe(long_table)

# =========================
# STATUS
# =========================
st.subheader("Regime Status")
st.write(regime)
