import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Engine Pro", layout="wide")

st.title("VIX Regime Engine (Enhanced Ladder Analytics)")

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
# EDITABLE SHORT ENTRY
# =========================
st.subheader("📉 Short Entry Ladder (editable)")

short_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
        "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic"
)

# =========================
# EDITABLE LONG ENTRY
# =========================
st.subheader("📈 Long Entry Ladder (editable)")

long_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [23, 24, 25, 26, 27, 28, 30],
        "Qty": [20, 40, 70, 100, 140, 180, 250]
    }),
    num_rows="dynamic"
)

# =========================
# SHORT EXIT (optional)
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
# HELPERS
# =========================
def build_ladder(df):
    df = df.copy()
    df["Notional"] = df["Qty"] * unit_value
    df["Accumulated_Qty"] = df["Qty"].cumsum()
    df["Accumulated_Notional"] = df["Notional"].cumsum()
    return df

def active(df, v):
    return df[df["VIX"] <= v]

# =========================
# BUILD TABLES
# =========================
short_table = build_ladder(short_entry)
long_table = build_ladder(long_entry)

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
    short_pos = short_qty * 0.4
    long_pos = 0

else:
    short_pos = 0
    long_pos = long_qty

# =========================
# COST MODEL
# =========================
trade_costs = (short_pos + long_pos) * spread

# =========================
# EXPOSURE
# =========================
short_notional = short_pos * unit_value
long_notional = long_pos * unit_value

net = long_notional - short_notional - trade_costs

# =========================
# RISK CONTROL
# =========================
if abs(net) > max_notional:
    scale = max_notional / abs(net)
    short_notional *= scale
    long_notional *= scale
    net *= scale

# =========================
# OUTPUT
# =========================
st.subheader("📊 Exposure")

st.write(f"Short Units: {short_pos:.0f}")
st.write(f"Long Units: {long_pos:.0f}")
st.write(f"Net Exposure: {net:.2f} €")
st.write(f"Spread Costs: {trade_costs:.2f} €")

# =========================
# TABLE OUTPUT
# =========================
st.subheader("📉 Short Ladder (with accumulation)")
st.dataframe(short_table)

st.subheader("📈 Long Ladder (with accumulation)")
st.dataframe(long_table)

# =========================
# STATUS
# =========================
st.subheader("Status")
st.write(regime)

if abs(net) > max_notional * 0.9:
    st.warning("Near Risk Limit")
else:
    st.success("Risk OK")
