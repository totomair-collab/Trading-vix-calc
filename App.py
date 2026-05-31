import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Engine v2", layout="wide")

st.title("VIX Regime Engine (Separated Exposure Model)")

# =========================
# INPUT
# =========================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)

equity = st.number_input("Kapital (€)", value=10000)

leverage = 10
max_notional = equity * leverage

# =========================
# YOUR EXACT LADDER
# =========================
short_ladder = pd.DataFrame({
    "VIX": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
    "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
})

long_ladder = pd.DataFrame({
    "VIX": [23, 24, 25, 26, 27, 28, 30],
    "Qty": [20, 40, 70, 100, 140, 180, 250]
})

# =========================
# REGIME DETECTION
# =========================
if vix < 20:
    regime = "REGIME 1 (SHORT BUILD)"
elif vix < 23:
    regime = "REGIME 2 (DE-RISK / NEUTRAL)"
else:
    regime = "REGIME 3 (LONG MODE)"

st.subheader("Regime")
st.info(regime)

# =========================
# ACTIVE EXPOSURE (NO CURVE MIXING)
# =========================
def active(df, v):
    return df[df["VIX"] <= v]["Qty"].sum()

short_raw = active(short_ladder, vix)
long_raw = active(long_ladder, vix)

# =========================
# REGIME SCALING (HARD SEPARATION)
# =========================
if regime == "REGIME 1 (SHORT BUILD)":
    short_pos = short_raw
    long_pos = 0

elif regime == "REGIME 2 (DE-RISK / NEUTRAL)":
    short_pos = short_raw * 0.4   # stark reduziert
    long_pos = 0

else:
    short_pos = 0
    long_pos = long_raw

# =========================
# NOTIONAL CONVERSION (IMPORTANT)
# =========================
# Annahme: 1 Qty = 1 "unit exposure"
# Skalierung auf echtes Risiko
unit_value = 100  # frei skalierbar (wichtig für dein Modell)

short_notional = short_pos * unit_value
long_notional = long_pos * unit_value

net_notional = long_notional - short_notional

# =========================
# RISK CONTROL (REALISTIC)
# =========================
if abs(net_notional) > max_notional:
    scale = max_notional / abs(net_notional)
    short_notional *= scale
    long_notional *= scale
    net_notional = long_notional - short_notional

# =========================
# OUTPUT
# =========================
st.subheader("Exposure")

st.write(f"Short Position: {short_pos:.0f} Units")
st.write(f"Long Position: {long_pos:.0f} Units")
st.write(f"Net Exposure (Notional): {net_notional:.0f} €")

st.write(f"Max Notional Allowed (10x): {max_notional:.0f} €")

# =========================
# STATUS
# =========================
st.subheader("Status")

if regime.startswith("SHORT"):
    st.write("Short-System aktiv (Mean Reversion)")
elif regime.startswith("DE-RISK"):
    st.write("Neutralphase – Risiko reduziert")
else:
    st.write("Long-System aktiv (Stress / Spike-Modus)")

# =========================
# WARNING
# =========================
if abs(net_notional) > max_notional * 0.9:
    st.warning("Nahe am Risk Limit")
else:
    st.success("Risk ok")
