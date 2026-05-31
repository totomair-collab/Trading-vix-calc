import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Regime Risk Engine", layout="wide")

st.title("VIX Regime Risk Engine (Full System)")

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
    regime = "REGIME 1 (SHORT BUILD)"
elif vix < 23:
    regime = "REGIME 2 (NEUTRAL / DE-RISK)"
else:
    regime = "REGIME 3 (LONG MODE)"

st.subheader("🧠 Regime")
st.info(regime)

# =========================
# EDITABLE SHORT ENTRY LADDER
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
# SHORT EXIT LADDER (PERCENT REDUCTION)
# =========================
st.subheader("📤 Short Exit Ladder (percentual)")

short_exit = st.data_editor(
    pd.DataFrame({
        "VIX": [20, 21, 22, 23],
        "Reduce_%": [0.1, 0.25, 0.5, 1.0]
    }),
    num_rows="dynamic"
)

# =========================
# LONG ENTRY LADDER
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
# HELPERS
# =========================
def active_qty(df, v):
    return df[df["VIX"] <= v]["Qty"].sum()

def exit_reduction(df, v):
    rows = df[df["VIX"] <= v]
    if len(rows) == 0:
        return 0
    return rows["Reduce_%"].iloc[-1]

# =========================
# BASE EXPOSURE
# =========================
short_raw = active_qty(short_entry, vix)
long_raw = active_qty(long_entry, vix)

TOTAL_SHORT_CAP = short_entry["Qty"].sum()
TOTAL_LONG_CAP = long_entry["Qty"].sum()

# =========================
# REGIME RULES
# =========================
if vix < 20:
    short_factor = 1.0
    long_factor = 0.0

elif vix < 23:
    short_factor = 0.5
    long_factor = 0.2

else:
    short_factor = 0.0
    long_factor = 1.0

short_pos = short_raw * short_factor
long_pos = long_raw * long_factor

# =========================
# EXIT LOGIC
# =========================
if vix >= 20 and vix < 23:
    reduction = exit_reduction(short_exit, vix)
    short_pos *= (1 - reduction)

# =========================
# HARD RISK CAPS
# =========================
max_exposure = max_risk

net = long_pos - short_pos
abs_net = abs(net)

if abs_net > max_exposure:
    scale = max_exposure / abs_net
    long_pos *= scale
    short_pos *= scale
    net = long_pos - short_pos

# =========================
# STEP LIMITS
# =========================
step_limits = {
    "REGIME 1 (SHORT BUILD)": 9,
    "REGIME 2 (NEUTRAL / DE-RISK)": 6,
    "REGIME 3 (LONG MODE)": 7
}

steps_short = len(short_entry[short_entry["VIX"] <= vix])
steps_long = len(long_entry[long_entry["VIX"] <= vix])

if regime == "REGIME 1 (SHORT BUILD)":
    if steps_short > step_limits[regime]:
        short_pos *= step_limits[regime] / steps_short

if regime == "REGIME 3 (LONG MODE)":
    if steps_long > step_limits[regime]:
        long_pos *= step_limits[regime] / steps_long

# =========================
# OUTPUT
# =========================
st.subheader("📊 Exposure")

st.write(f"Short Position: {short_pos:.0f}")
st.write(f"Long Position: {long_pos:.0f}")
st.write(f"Net Exposure: {net:.0f}")

# =========================
# RISK STATUS
# =========================
st.subheader("⚙️ Risk")

if abs_net > max_exposure:
    st.error("Risk Limit überschritten")
else:
    st.success("Risk innerhalb Limit")

# =========================
# INTERPRETATION
# =========================
st.subheader("📍 System Status")

if regime.startswith("SHORT"):
    st.write("Short-Engine aktiv")
elif regime.startswith("NEUTRAL"):
    st.write("De-Risk Phase – keine Richtungsentscheidung")
else:
    st.write("Long-Engine aktiv")
