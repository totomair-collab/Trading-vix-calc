import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Ladder Control Panel", layout="centered")

st.title("VIX Ladder System – Editierbares Risk Control Panel")

# =========================
# AUFBAU (FIX)
# =========================
st.subheader("📈 Aufbau (Stückzahlen)")

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

st.write(f"Gesamtposition: {total_qty}")
st.write(f"Ø Einstieg: {avg_price:.2f}")

# =========================
# MARKT
# =========================
st.subheader("📊 Markt")

vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)

# =========================
# EDITIERBARE ABBAU-TABELLE
# =========================
st.subheader("📉 Abbau-Logik (EDITIERBAR)")

default_exit = pd.DataFrame([
    {"stufe": 1, "vix_zone": "26 → 24", "reduce_factor": 0.10},
    {"stufe": 2, "vix_zone": "24 → 22.5", "reduce_factor": 0.25},
    {"stufe": 3, "vix_zone": "22.5 → 21", "reduce_factor": 0.45},
    {"stufe": 4, "vix_zone": "21 → 20", "reduce_factor": 0.65},
    {"stufe": 5, "vix_zone": "20 → 18.5", "reduce_factor": 0.80},
    {"stufe": 6, "vix_zone": "< 18.5", "reduce_factor": 1.00},
])

exit_df = st.data_editor(
    default_exit,
    num_rows="dynamic",
    use_container_width=True
)

# =========================
# LIVE ABBAU-BERECHNUNG
# =================
