import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Symmetric Ladder", layout="centered")

st.title("VIX Ladder System (Symmetrisch: Aufbau + Abbau)")

# =========================
# BASIS 8-STUFEN
# =========================
st.subheader("📊 Aufbau-Logik")

build = [
    {"vix": 18.3, "weight": 0.10},
    {"vix": 18.8, "weight": 0.15},
    {"vix": 19.3, "weight": 0.20},
    {"vix": 20.0, "weight": 0.25},
    {"vix": 21.0, "weight": 0.30},
    {"vix": 22.5, "weight": 0.40},
    {"vix": 24.0, "weight": 0.50},
    {"vix": 26.0, "weight": 0.60},
]

df_build = pd.DataFrame(build)
st.dataframe(df_build)

# =========================
# ABBAU-LOGIK
# =========================
st.subheader("📉 Abbau-Logik")

exit_rules = [
    {"zone": "26 → 24", "reduce": "10%"},
    {"zone": "24 → 22.5", "reduce": "15%"},
    {"zone": "22.5 → 21", "reduce": "20%"},
    {"zone": "21 → 20", "reduce": "25%"},
    {"zone": "20 → 18.5", "reduce": "30%"},
    {"zone": "< 18.5", "reduce": "100% (flat)"},
]

df_exit = pd.DataFrame(exit_rules)
st.dataframe(df_exit)

# =========================
# POSITION INPUT
# =========================
st.write("---")
st.subheader("📌 Position Simulation")

total_position = st.number_input("Gesamtposition (Kontrakte)", value=1000)

vix = st.number_input("Aktueller VIX", value=20.0, step=0.1)

# =========================
# AUFBAU PHASE
# =========================
if vix <= 18.8:
    phase = "LOW / NO BUILD"
elif vix <= 20:
    phase = "EARLY BUILD"
elif vix <= 22.5:
    phase = "BUILDING"
elif vix <= 24:
    phase = "FULL BUILD"
elif vix <= 26:
    phase = "MAX RISK BUILD"
else:
    phase = "STOP BUILD"

st.subheader("📈 Phase")
st.info(phase)

# =========================
# ABBAU PHASE
# =========================
if vix > 26:
    reduce = 0.0
elif vix > 24:
    reduce = 0.10
elif vix > 22.5:
    reduce = 0.25
elif vix > 21:
    reduce = 0.45
elif vix > 20:
    reduce = 0.65
elif vix > 18.5:
    reduce = 0.80
else:
    reduce = 1.0

allowed_position = total_position * reduce

st.subheader("📉 Aktueller Abbau-Zustand")
st.write(f"Erlaubte Position: {allowed_position:.0f}")

if total_position > allowed_position:
    st.warning("Position sollte reduziert werden")
else:
    st.success("Position im Rahmen")

# =========================
# VISUELLE KLARHEIT
# =========================
st.write("---")
st.subheader("🧠 System-Interpretation")

if vix < 18.5:
    st.success("Normalbereich / volle Reduktion möglich")
elif vix < 21:
    st.info("ruhige Zone / kontrollierter Aufbau")
elif vix < 24:
    st.warning("Stresszone / vorsichtig skalieren")
else:
    st.error("Extremzone / kein Aufbau mehr")
