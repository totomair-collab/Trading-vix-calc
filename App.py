
import streamlit as st

st.set_page_config(page_title="Trading Rechner", layout="centered")

st.title("Trading Rechner (DCA + Risiko + PnL)")

# ----------------------------
# Session State
# ----------------------------
if "orders" not in st.session_state:
    st.session_state.orders = []

# ----------------------------
# Order Eingabe
# ----------------------------
st.subheader("Orders hinzufügen")

col1, col2 = st.columns(2)

with col1:
    price = st.number_input("Preis", value=18.0, step=0.01)

with col2:
    qty = st.number_input("Menge", value=100, step=1)

if st.button("Order hinzufügen"):
    st.session_state.orders.append({"price": price, "qty": qty})

if st.session_state.orders:
    if st.button("Letzte Order löschen"):
        st.session_state.orders.pop()

# ----------------------------
# Orders anzeigen
# ----------------------------
st.subheader("Orders")

if st.session_state.orders:
    for i, o in enumerate(st.session_state.orders, 1):
        st.write(f"{i}. Preis: {o['price']} | Menge: {o['qty']}")
else:
    st.write("Keine Orders vorhanden")

# ----------------------------
# Berechnung
# ----------------------------
if st.session_state.orders:

    total_qty = sum(o["qty"] for o in st.session_state.orders)
    total_cost = sum(o["price"] * o["qty"] for o in st.session_state.orders)
    avg_price = total_cost / total_qty

    st.subheader("Position")

    st.write(f"Gesamtmenge: {total_qty}")
    st.write(f"Durchschnittspreis: {avg_price:.4f}")

    # ----------------------------
    # WARNUNG > 1000 Stück
    # ----------------------------
    if total_qty > 1000:
        st.error("⚠️ KRITISCH: Mehr als 1000 Stück im Trade!")
        st.markdown("## ❗ POSITION ZU GROSS ❗")
    else:
        st.success("Positionsgröße im normalen Bereich")

    # ----------------------------
    # Marktpreis
    # ----------------------------
    market_price = st.number_input("Aktueller Marktpreis", value=18.0, step=0.01)

    # Long / Short
    direction = st.radio("Richtung", ["Long", "Short"])

    if direction == "Long":
        pnl = (market_price - avg_price) * total_qty
    else:
        pnl = (avg_price - market_price) * total_qty

    pnl_percent = (pnl / (avg_price * total_qty)) * 100

    st.subheader("PnL")
    st.write(f"Unrealized PnL: {pnl:.2f} €")
    st.write(f"PnL: {pnl_percent:.2f} %")

    # ----------------------------
    # Risiko / Stop Loss
    # ----------------------------
    st.subheader("Risiko-Management")

    account_size = st.number_input("Kontogröße (€)", value=10000)

    stop_loss = st.number_input("Stop-Loss Preis", value=17.0, step=0.01)

    if direction == "Long":
        risk = (avg_price - stop_loss) * total_qty
    else:
        risk = (stop_loss - avg_price) * total_qty

    risk_percent = (risk / account_size) * 100

    st.write(f"Risiko bis Stop: {risk:.2f} €")
    st.write(f"Risiko vom Konto: {risk_percent:.2f} %")

    # Risiko Warnung
    if risk_percent > 5:
        st.warning("⚠️ Hohes Risiko (>5% vom Konto)")

    # ----------------------------
    # Reset
    # ----------------------------
    if st.button("Alles löschen"):
        st.session_state.orders = []
