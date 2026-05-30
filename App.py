import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Ladder System", layout="centered")

st.title("VIX 8-Stufen System (Aufbau + Abbau + Regime)")

# =========================
# 8-STUFEN (EDITIERBAR)
# =========================
st.subheader("📊 8-Stufen Aufbau")

default_data = {
    "vix": [18.3, 18.8, 19.3, 20.0, 21.0, 22.5, 24.0, 26.0],
    "qty": [50, 60, 75, 90, 110, 140, 180, 230]
}

df = st.data_editor(
    pd.DataFrame(default_data),
    num_rows="dynamic",
    use_container_width=True
)

total_qty = df["qty"].sum()
total_cost = (df["vix"] * df["qty"]).sum()
avg_price = total_cost / total_qty

st.write(f"Gesamtposition: {total_qty}")
st.write(f"Ø Einstieg: {avg_price:.2f}")

# =========================
# MARKTPREIS + PnL
# =========================
st.subheader("📈 Markt")

market_price = st.number_input("Aktueller VIX", value=18.0, step=0.1)
direction = st.radio("Richtung", ["Short", "Long"])

if direction == "Short":
    pnl = (avg_price - market_price) * total_qty
else:
    pnl = (market_price - avg_price) * total_qty

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
    ["Contango (normal)", "Flat", "Backwardation (Stress)"]
)

event_level = st.selectbox(
    "News-Level",
    ["Keine Events", "Makro-News", "Krisen-News"]
)

vix = market_price

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

structure_score = {
    "Contango (normal)": 10,
    "Flat": 40,
    "Backwardation (Stress)": 70
}[term_structure]

event_score = {
    "Keine Events": 5,
    "Makro-News": 25,
    "Krisen-News": 60
}[event_level]

regime_score = (
    0.5 * vix_score +
    0.2 * trend_score +
    0.2 * structure_score +
    0.1 * event_score
)

# =========================
# REGIME CLASSIFICATION
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
# POSITION PHASE LOGIC
# =========================
st.subheader("⚙️ Phase (Aufbau / Halten / Abbau)")

if vix <= 21:
    phase = "AUFBAU / HOLD"
elif vix <= 24:
    phase = "VOLLE POSITION / HOLD"
elif vix <= 26:
    phase = "BEGINN ABBAU"
elif vix <= 24:
    phase = "ABBAU"
elif vix <= 22.5:
    phase = "ABBAU BESCHLEUNIGT"
elif vix <= 20:
    phase = "STARKER ABBAU"
else:
    phase = "FLAT / MINIMAL EXPOSURE"

st.write(f"Aktuelle Phase: {phase}")

# =========================
# ABBAU LOGIK
# =========================
st.subheader("📉 Abbau-Logik (wenn VIX fällt)")

if vix <= 18.5:
    de_risk = "REST POSITION GLATTSTELLEN"
    factor = 0.0
elif vix <= 20:
    de_risk = "25% ABBRUCH"
    factor = 0.25
elif vix <= 21:
    de_risk = "20% ABBRUCH"
    factor = 0.45
elif vix <= 22.5:
    de_risk = "15% ABBRUCH"
    factor = 0.60
elif vix <= 24:
    de_risk = "10% ABBRUCH"
    factor = 0.75
else:
    de_risk = "KEIN ABBRUCH"
    factor = 1.0

adjusted_position = total_qty * factor

st.write(de_risk)
st.write(f"Erlaubte Restposition: {adjusted_position:.0f}")

if total_qty > adjusted_position:
    st.warning("⚠️ Position sollte reduziert werden")
else:
    st.success("Position im Zielbereich")

# =========================
# RISK CHECK
# =========================
st.subheader("🚨 Risiko")

if vix > 25 and total_qty > 1000:
    st.error("EXTREMES RISIKO: hohe Volatilität + große Position")
elif vix > 20:
    st.warning("Erhöhtes Risiko")
else:
    st.success("Normales Umfeld")
