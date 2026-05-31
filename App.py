import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Engine Pro", layout="wide")

st.title("VIX Regime Engine (Editable + Spread + Accumulation)")

# =========================
# INPUT
# =========================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)
equity = st.number_input("Kapital (€)", value=10000)
leverage = 10

spread = 0.13  # FIXED spread per trade

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
# SHORT ENTRY LADDER (EDITABLE)
# =========================
st.subheader("📉 Short Entry Ladder")

short_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
        "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic"
)

# =========================
# LONG ENTRY LADDER (EDITABLE)
# =========================
st.subheader("📈 Long Entry Ladder")

long_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [23, 24, 25, 26, 27, 28, 30],
        "Qty": [20, 40, 70, 100, 140, 180, 250]
    }),
    num_rows="dynamic"
)

# =========================
# SHORT EXIT LADDER
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
def active(df, v):
    return df[df["VIX"] <= v].copy()

def add_accumulated(df):
    df = df.copy()
    df["Accumulated_Qty"] = df["Qty"].cumsum()
    return df

# =========================
# ACTIVE DATA
# =========================
short_active = active(short_entry, vix)
long_active = active(long_entry, vix)

short_active = add_accumulated(short_active)
long_active = add_accumulated(long_active)

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
# COST MODEL (SPREAD)
# =========================
total_trades = short_pos + long_pos

costs = total_trades * spread

# =========================
# RISK MODEL
# =========================
unit_value = 100

short_notional = short_pos * unit_value
long_notional = long_pos * unit_value

net = long_notional - short_notional

# adjust for costs
net_after_costs = net - costs

# =========================
# LIMIT CONTROL
# =========================
if abs(net_after_costs) > max_notional:
    scale = max_notional / abs(net_after_costs)
    short_notional *= scale
    long_notional *= scale
    net_after_costs *= scale

# =========================
# OUTPUT
# =========================
st.subheader("📊 Exposure")

st.write(f"Short Units: {short_pos:.0f}")
st.write(f"Long Units: {long_pos:.0f}")

st.write(f"Net Exposure: {net_after_costs:.0f} €")
st.write(f"Spread Costs: {costs:.2f} €")

st.subheader("📉 Tabellen (mit Akkumulation)")

st.write("Short Active")
st.dataframe(short_active)

st.write("Long Active")
st.dataframe(long_active)

# =========================
# STATUS
# =========================
st.subheader("Status")

st.write(regime)

if abs(net_after_costs) > max_notional * 0.9:
    st.warning("Nahe am Risk Limit")
else:
    st.success("Risk ok")
