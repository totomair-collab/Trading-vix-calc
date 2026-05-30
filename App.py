import streamlit as st
import import as pd

st.set_page_config(page_title="VIX Trading System", layout="centered")

st.title("VIX Trading System – 8 Stufen + Regime")

# =========================
# 8-STUFEN (EDITIERBAR)
# =========================
st.subheader("📊 8-Stufen-Strategie (editierbar)")

default_data = {
    "vix": [18.29, 18.39, 18.59, 18.89, 19.29, 19.79, 20.39, 21.09],
    "qty": [50, 75, 125, 200, 300, 425, 575, 750]
}

df = st.data_editor(
    pd.DataFrame(default_data),
    num_rows="dynamic",
    use_container_width=True
)

# Berechnung
total_qty = df["qty"].sum()
total_cost = (df["vix"] * df["qty"]).sum()
avg_price = total_cost / total_qty

st.write("---")
st.subheader("📌 Positionsdaten")

st.write(f"Gesamtmenge: {total_qty}")
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

vix = market_price

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

# =========================
# SCORE SYSTEM
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
# REGIME OUTPUT
# =========================
st.subheader("📊 Markt-Regime")

if regime_score < 30:
    regime = "CALM"
    st.success(f"{regime} | Score: {regime_score:.1f}")

elif regime_score < 50:
    regime = "NORMAL"
    st.info(f"{regime} | Score: {regime_score:.1f}")

elif regime_score < 70:
    regime = "STRESS"
    st.warning(f"{regime} | Score: {regime_score:.1f}")

else:
    regime = "CRISIS"
    st.error(f"{regime} | Score: {regime_score:.1f}")

# =========================
# REGIME STEUERUNG
# =========================
st.subheader("⚙️ Risiko-Steuerung")

if regime == "CALM":
    factor = 1.0
    allow_scaling = True
elif regime == "NORMAL":
    factor = 0.8
    allow_scaling = True
elif regime == "STRESS":
    factor = 0.5
    allow_scaling = False
else:
    factor = 0.2
    allow_scaling = False

adjusted_limit = total_qty * factor

st.write(f"Original Position: {total_qty}")
st.write(f"Regime-Limit: {adjusted_limit:.0f}")

if total_qty > adjusted_limit:
    st.error("⚠️ Position zu groß für aktuelles Regime")
else:
    st.success("Position im erlaubten Bereich")

if not allow_scaling:
    st.warning("⚠️ Skalierung deaktiviert im aktuellen Regime")

# =========================
# RISIKO-ALERT
# =========================
st.write("---")
st.subheader("🚨 Risiko-Check")

if vix > 25 and total_qty > 1000:
    st.error("EXTREMES RISIKO: hohe Volatilität + große Position")
elif vix > 20:
    st.warning("Erhöhtes Volatilitätsrisiko")
else:
    st.success("Normales Umfeld")
