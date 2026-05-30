import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Risk Ladder System", layout="centered")

st.title("VIX Ladder System – Optimiert (Aufbau + Abbau + Risiko)")

# =========================
# AUFBAU (STÜCKZAHLEN)
# =========================
st.subheader("📈 Aufbau-Logik (Stückzahlen)")

build = [
    {"vix": 18.3, "qty": 50},
    {"vix": 18.8, "qty": 60},
    {"vix": 19.3, "qty": 75},
    {"vix": 20.0, "qty": 90},
    {"vix": 21.0, "qty": 110},
    {"vix": 22.5, "qty": 140},
    {"vix": 24.0, "qty": 180},
    {"vix": 26.0, "qty": 230},
]

df_build = pd.DataFrame(build)
st.dataframe(df_build)

total_qty = df_build["qty"].sum()
total_cost = (df_build["vix"] * df_build["qty"]).sum()
avg_price = total_cost / total_qty

st.write(f"Gesamtposition: {total_qty}")
st.write(f"Ø Einstieg: {avg_price:.2f}")

# =========================
# MARKT INPUT
# =========================
st.subheader("📊 Markt")

market_vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)

direction = st.radio("Richtung", ["Short", "Long"])

if direction == "Short":
    pnl = (avg_price - market_vix) * total_qty
else:
    pnl = (market_vix - avg_price) * total_qty

st.write(f"PnL: {pnl:.2f}")

# =========================
# REGIME INPUT
# =========================
st.write("---")
st.subheader("🧠 Regime-System")

market_trend = st.selectbox(
    "Markttrend",
    ["Uptrend", "Sideways", "Downtrend"]
)

term_structure = st.selectbox(
    "VIX Struktur",
    ["Contango", "Flat", "Backwardation"]
)

event_level = st.selectbox(
    "News-Level",
    ["Keine", "Makro", "Krise"]
)

vix = market_vix

# =========================
# VIX SCORE
# =========================
if vix < 12:
    vix_score = 10
elif vix < 15:
    vix_score = 20
elif vix < 20:
    vix_score = 35
elif vix < 25:
    vix_score = 55
elif vix < 35:
    vix_score = 75
else:
    vix_score = 95

trend_score = {"Uptrend": 10, "Sideways": 30, "Downtrend": 50}[market_trend]

structure_score = {"Contango": 10, "Flat": 40, "Backwardation": 70}[term_structure]

event_score = {"Keine": 5, "Makro": 25, "Krise": 60}[event_level]

regime_score = (
    0.5 * vix_score +
    0.2 * trend_score +
    0.2 * structure_score +
    0.1 * event_score
)

# =========================
# REGIME OUTPUT
# =========================
st.subheader("📊 Markt-Regime")

if regime_score < 30:
    regime = "CALM"
    st.success(f"{regime} | {regime_score:.1f}")

elif regime_score < 50:
    regime = "NORMAL"
    st.info(f"{regime} | {regime_score:.1f}")

elif regime_score < 70:
    regime = "STRESS"
    st.warning(f"{regime} | {regime_score:.1f}")

else:
    regime = "CRISIS"
    st.error(f"{regime} | {regime_score:.1f}")

# =========================
# ABBAU-LOGIK (PROZENTBASIERT)
# =========================
st.subheader("📉 Abbau-Logik")

if vix > 26:
    reduce_factor = 0.0
    label = "Komplett raus"
elif vix > 24:
    reduce_factor = 0.10
    label = "10% reduzieren"
elif vix > 22.5:
    reduce_factor = 0.25
    label = "25% reduzieren"
elif vix > 21:
    reduce_factor = 0.45
    label = "45% reduziert"
elif vix > 20:
    reduce_factor = 0.65
    label = "65% reduziert"
elif vix > 18.5:
    reduce_factor = 0.80
    label = "80% reduziert"
else:
    reduce_factor = 1.0
    label = "volle Position erlaubt"

allowed_position = total_qty * reduce_factor

st.write(label)
st.write(f"Erlaubte Position: {allowed_position:.0f}")

if total_qty > allowed_position:
    st.warning("⚠️ Position sollte reduziert werden")
else:
    st.success("Position im Rahmen")

# =========================
# RISIKO-KONTROLLE
# =========================
st.subheader("🚨 Risiko-Check")

max_safe_position = 1000

if total_qty > max_safe_position and vix > 25:
    st.error("EXTREMES RISIKO: große Position + hohe Volatilität")
elif vix > 25:
    st.warning("Hohe Volatilität")
else:
    st.success("Normales Risiko")

# =========================
# SYSTEM INTERPRETATION
# =========================
st.write("---")
st.subheader("🧠 System-Zustand")

if vix <= 18.5:
    st.success("Aufbauzone / niedrige Volatilität")
elif vix <= 21:
    st.info("Normaler Aufbau / Halten")
elif vix <= 24:
    st.warning("Stresszone / vorsichtig reduzieren")
else:
    st.error("Extremzone / Risikoabbau aktiv")
