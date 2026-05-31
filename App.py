import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Trading Engine", layout="wide")

st.title("VIX Regime Trading Engine (Editable Ladder System)")

# =========================
# INPUT
# =========================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)
equity = st.number_input("Kontogröße ($)", value=100000)
risk_pct = st.slider("Max Risiko %", 1, 10, 3)

max_risk = equity * risk_pct / 100

# =========================
# REGIME
# =========================
if vix < 20:
    regime = "REGIME 1: NORMAL (SHORT MODE)"
elif vix < 24:
    regime = "REGIME 2: TRANSITION (DE-RISK)"
else:
    regime = "REGIME 3: STRESS (LONG MODE)"

st.subheader("🧠 Regime Status")
st.info(regime)

# =========================
# DEFAULT TABLES (EDITABLE)
# =========================

st.subheader("📉 Short Entry Ladder (Regime 1)")

short_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [16, 16.5, 17, 17.5, 18, 18.5, 19, 19.5, 20],
        "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic"
)

st.subheader("📤 Short Exit Ladder (Regime 2)")
short_exit = st.data_editor(
    pd.DataFrame({
        "VIX": [20, 21, 22, 23, 24],
        "Reduce_%": [0.1, 0.25, 0.5, 0.75, 1.0]
    }),
    num_rows="dynamic"
)

st.subheader("📈 Long Entry Ladder (Regime 3)")
long_entry = st.data_editor(
    pd.DataFrame({
        "VIX": [24, 25, 26, 27, 28, 30],
        "Qty": [30, 50, 80, 120, 160, 220]
    }),
    num_rows="dynamic"
)

# =========================
# LOGIC FUNCTIONS
# =========================

def calc_short_exposure(vix, df):
    active = df[df["VIX"] <= vix]
    return active["Qty"].sum()

def calc_long_exposure(vix, df):
    active = df[df["VIX"] <= vix]
    return active["Qty"].sum()

def calc_reduction(vix, df):
    active = df[df["VIX"] <= vix]
    if len(active) == 0:
        return 0
    return active["Reduce_%"].iloc[-1]

# =========================
# CALCULATION
# =========================

short_qty = calc_short_exposure(vix, short_entry)
long_qty = calc_long_exposure(vix, long_entry)

# Transition logic
if vix < 20:
    short_effective = short_qty
    long_effective = 0

elif vix < 24:
    reduction = calc_reduction(vix, short_exit)
    short_effective = short_qty * (1 - reduction)
    long_effective = 0.2 * long_qty

else:
    short_effective = 0
    long_effective = long_qty

net_exposure = long_effective - short_effective

# =========================
# DISPLAY
# =========================

st.subheader("📊 Exposure Overview")

st.write(f"Short Exposure: {short_effective:.0f}")
st.write(f"Long Exposure: {long_effective:.0f}")
st.write(f"Net Exposure: {net_exposure:.0f}")

# =========================
# RISK CONTROL
# =========================

st.subheader("⚙️ Risk Control")

abs_exposure = abs(net_exposure)

if abs_exposure > max_risk:
    st.error("⚠️ Risiko überschritten → Position reduzieren")
else:
    st.success("Risiko im Rahmen")

# =========================
# INTERPRETATION
# =========================

st.subheader("📍 System Status")

if regime.startswith("NORMAL"):
    st.write("Short-System aktiv. Aufbau erlaubt.")
elif regime.startswith("TRANSITION"):
    st.write("Reduktion Shorts + vorsichtige Long-Hedges.")
else:
    st.write("Shorts deaktiviert. Long-System aktiv.")
