import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Risk Control Panel", layout="centered")

st.title("VIX Ladder System – Safe Mode Control Panel")

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
# SAFE MODE VALIDATION
# =========================
st.subheader("🛡 Safe Mode Check")

errors = []

# 1. Stufenprüfung
if not exit_df["stufe"].is_monotonic_increasing:
    errors.append("Stufen sind nicht aufsteigend sortiert")

# 2. Faktorprüfung
if exit_df["reduce_factor"].min() < 0 or exit_df["reduce_factor"].max() > 1:
    errors.append("Reduce-Faktor muss zwischen 0 und 1 liegen")

# 3. Duplikate
if exit_df["stufe"].duplicated().any():
    errors.append("Doppelte Stufen vorhanden")

if errors:
    for e in errors:
        st.error(e)
    st.stop()
else:
    st.success("Abbau-Tabelle ist gültig")

# =========================
# ABBAU LOGIK
# =========================
def get_allowed_factor(vix, df):
    if vix > 26:
        return float(df.loc[0, "reduce_factor"])
    elif vix > 24:
        return float(df.loc[1, "reduce_factor"])
    elif vix > 22.5:
        return float(df.loc[2, "reduce_factor"])
    elif vix > 21:
        return float(df.loc[3, "reduce_factor"])
    elif vix > 20:
        return float(df.loc[4, "reduce_factor"])
    elif vix > 18.5:
        return float(df.loc[5, "reduce_factor"])
    else:
        return float(df.loc[5, "reduce_factor"])

factor = get_allowed_factor(vix, exit_df)

allowed_qty = total_qty * factor

st.subheader("📉 Positionskontrolle")
st.write(f"Erlaubte Position: {allowed_qty:.0f}")

if total_qty > allowed_qty:
    st.warning("⚠️ Position über Limit → reduzieren")
else:
    st.success("Position im Rahmen")

# =========================
# SYSTEM STATUS
# =========================
st.write("---")
st.subheader("🧠 Systemstatus")

if vix <= 18.5:
    st.success("Normalzone – volle Position erlaubt")
elif vix <= 21:
    st.info("Aufbau-/Haltezone")
elif vix <= 24:
    st.warning("Stresszone – vorsichtig reduzieren")
else:
    st.error("Extremzone – Risikoabbau aktiv")

# =========================
# DEBUG VIEW
# =========================
st.write("---")
st.subheader("🔧 Debug Ansicht")

st.dataframe(exit_df)
