import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Controlled Ladder", layout="wide")

st.title("VIX Regime Controlled Entry System")

# ======================
# INPUT
# ======================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)

# ======================
# YOUR LADDER (EXACT CSV)
# ======================
ladder = pd.DataFrame({
    "VIX": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
    "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
})

TOTAL_CAPACITY = ladder["Qty"].sum()

# ======================
# REGIME
# ======================
if vix < 20:
    regime = "REGIME 1 (NORMAL SHORT BUILD)"
elif vix < 23:
    regime = "REGIME 2 (TRANSITION - REDUCE RISK)"
else:
    regime = "REGIME 3 (STRESS - NO NEW SHORTS)"

st.subheader("Regime")
st.info(regime)

# ======================
# EXPOSURE LOGIC
# ======================

def active_ladder(v):
    return ladder[ladder["VIX"] <= v]

active = active_ladder(vix)

raw_exposure = active["Qty"].sum()

# ======================
# HARD LIMITS
# ======================

MAX_EXPOSURE = TOTAL_CAPACITY * 0.8

if regime == "REGIME 1 (NORMAL SHORT BUILD)":
    exposure = min(raw_exposure, MAX_EXPOSURE)

elif regime == "REGIME 2 (TRANSITION - REDUCE RISK)":
    exposure = min(raw_exposure * 0.5, MAX_EXPOSURE * 0.6)

else:
    exposure = 0  # no new shorts

# ======================
# STEP LIMIT CONTROL
# ======================

max_steps_allowed = {
    "REGIME 1 (NORMAL SHORT BUILD)": 9,
    "REGIME 2 (TRANSITION - REDUCE RISK)": 6,
    "REGIME 3 (STRESS - NO NEW SHORTS)": 0
}

steps_used = len(active)
steps_allowed = max_steps_allowed[regime]

if steps_used > steps_allowed:
    exposure *= steps_allowed / steps_used

# ======================
# DISPLAY
# ======================
st.subheader("Exposure")

st.write(f"Aktive Stufen: {steps_used} / 9")
st.write(f"Short Exposure (adjusted): {exposure:.0f}")
st.write(f"Max Allowed: {MAX_EXPOSURE:.0f}")

# ======================
# SAFETY CHECK
# ======================
if exposure > MAX_EXPOSURE:
    st.error("EXPOSURE LIMIT BREACHED")
else:
    st.success("Exposure within safe limits")

# ======================
# TABLE VIEW
# ======================
st.subheader("Ladder (your structure)")
st.dataframe(ladder)
