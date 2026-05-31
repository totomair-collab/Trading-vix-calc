import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Exposure System", layout="centered")

st.title("VIX Regime Exposure System (No Flip Model)")

# =========================
# INPUT
# =========================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)

equity = st.number_input("Kontogröße ($)", value=100000)
risk_pct = st.slider("Max Risiko %", 1, 10, 3)

max_risk = equity * risk_pct / 100

# =========================
# REGIME DETECTION
# =========================
if vix < 20:
    regime = "NORMAL (SHORT EDGE)"
elif vix < 24:
    regime = "TRANSITION (DE-RISK)"
else:
    regime = "STRESS (LONG HEDGE MODE)"

st.subheader("🧠 Regime")
st.info(regime)

# =========================
# BASE SHORT LADDER (NUR NORMAL)
# =========================
short_ladder = [
    (16.0, 20),
    (16.5, 25),
    (17.0, 35),
    (17.5, 50),
    (18.0, 70),
    (18.5, 95),
    (19.0, 130),
    (19.5, 180),
    (20.0, 250),
]

df_short = pd.DataFrame(short_ladder, columns=["VIX", "Qty"])

# =========================
# BASE LONG LADDER (NUR STRESS)
# =========================
long_ladder = [
    (24, 30),
    (25, 50),
    (26, 80),
    (27, 120),
    (28, 160),
    (30, 220),
]

df_long = pd.DataFrame(long_ladder, columns=["VIX", "Qty"])

# =========================
# EXPOSURE FUNCTION
# =========================
def short_exposure(vix):
    if vix < 20:
        return 1.0
    elif vix < 22:
        return 0.5
    elif vix < 24:
        return 0.2
    else:
        return 0.0

def long_exposure(vix):
    if vix < 22:
        return 0.0
    elif vix < 24:
        return 0.2
    elif vix < 26:
        return 0.4
    elif vix < 28:
        return 0.7
    else:
        return 1.0

# =========================
# CALC EXPOSURE
# =========================
s_exp = short_exposure(vix)
l_exp = long_exposure(vix)

short_qty = df_short["Qty"].sum() * s_exp
long_qty = df_long["Qty"].sum() * l_exp

# =========================
# DISPLAY
# =========================
st.subheader("📊 Exposure")

st.write(f"Short Exposure: {short_qty:.0f}")
st.write(f"Long Exposure: {long_qty:.0f}")

net = long_qty - short_qty
st.write(f"Net Exposure: {net:.0f}")

# =========================
# RISK CONTROL
# =========================
st.subheader("⚙️ Risk Control")

total_abs = abs(net)

if total_abs > max_risk:
    st.error("⚠️ Risiko über Limit → Position reduzieren")
else:
    st.success("Risiko im Rahmen")

# =========================
# INTERPRETATION
# =========================
st.subheader("📍 Interpretation")

if regime.startswith("NORMAL"):
    st.write("Short-Edge aktiv. Kein Long-Aufbau.")
elif regime.startswith("TRANSITION"):
    st.write("Reduziere Shorts, aber kein Richtungswechsel.")
else:
    st.write("Shorts geschlossen. Long nur als Stress-Hedge.")
