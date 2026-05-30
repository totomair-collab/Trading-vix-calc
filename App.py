import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Risk Control System", layout="centered")

st.title("VIX Ladder System – Optimized State Engine")

# =========================
# AUFBAU (FIX)
# =========================
st.subheader("📈 Aufbau (Stückzahlen, Stufe 1–8)")

build = [
    {"stufe": 1, "vix": 18.3, "qty": 50},
    {"stufe": 2, "vix": 18.8, "qty": 60},
    {"stufe": 3, "vix": 19.3, "qty": 75},
    {"stufe": 4, "vix": 20.0, "qty": 90},
    {"stufe": 5, "vix": 21.0, "qty": 110},
    {"stufe": 6, "vix": 22.5, "qty": 140},
    {"stufe": 7, "vix": 24.0, "qty": 180},
    {"stufe": 8, "vix": 26.0, "qty": 230},
]

df_build = pd.DataFrame(build)
st.dataframe(df_build)

total_qty = df_build["qty"].sum()
avg_price = (df_build["vix"] * df_build["qty"]).sum() / total_qty

# =========================
# MARKT
# =========================
st.subheader("📊 Markt")

vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)

direction = st.radio("Richtung", ["Short", "Long"])

pnl = (avg_price - vix) * total_qty if direction == "Short" else (vix - avg_price) * total_qty

st.write(f"Gesamtposition: {total_qty}")
st.write(f"Ø Einstieg: {avg_price:.2f}")
st.write(f"PnL: {pnl:.2f}")

# =========================
# AKTIVE AUFBAU STUFE
# =========================
active_build = max([s["stufe"] for s in build if vix >= s["vix"]], default=0)

# =========================
# ABBAU LOGIK
# =========================
def get_exit_factor(v):
    if v > 26:
        return 0.0
    elif v > 24:
        return 0.10
    elif v > 22.5:
        return 0.25
    elif v > 21:
        return 0.45
    elif v > 20:
        return 0.65
    elif v > 18.5:
        return 0.80
    else:
        return 1.0

factor = get_exit_factor(vix)
allowed_qty = total_qty * factor

# =========================
# AKTIVE ABBAU STUFE
# =========================
if vix > 26:
    active_exit = 0
elif vix > 24:
    active_exit = 1
elif vix > 22.5:
    active_exit = 2
elif vix > 21:
    active_exit = 3
elif vix > 20:
    active_exit = 4
elif vix > 18.5:
    active_exit = 5
else:
    active_exit = 6

# =========================
# STATE ENGINE (NEU – WICHTIG)
# =========================
st.write("---")
st.subheader("🧠 System State Engine")

if vix <= 18.5:
    state = "STABLE / FULL EXPOSURE OK"
elif vix <= 21:
    state = "BUILD PHASE"
elif vix <= 24:
    state = "STRESS PHASE"
else:
    state = "CRITICAL / DE-RISK"

# =========================
# DISPLAY STATE
# =========================
st.info(f"STATE: {state}")

st.write(f"Aufbau-Stufe: {active_build}/8")
st.write(f"Abbau-Stufe: {active_exit}/6")

# =========================
# RISK CONTROL
# =========================
st.subheader("⚙️ Risk Control")

st.write(f"Erlaubte Position: {allowed_qty:.0f}")

if total_qty > allowed_qty:
    st.warning("⚠️ Position reduzieren")
else:
    st.success("Position im Rahmen")

# =========================
# SYSTEM INTERPRETATION (FINAL LAYER)
# =========================
st.write("---")
st.subheader("📊 Interpretation Layer")

if vix < 18.5:
    st.success("ruhiger Markt – System arbeitet normal")
elif vix < 21:
    st.info("moderate Volatilität – kontrollierter Aufbau")
elif vix < 24:
    st.warning("erhöhte Volatilität – Risiko aktiv managen")
else:
    st.error("Stress / Krise – Kapital schützen wichtiger als Position")
