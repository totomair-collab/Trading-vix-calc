import streamlit as st

st.set_page_config(page_title="Trading & VIX Risk Tool", layout="centered")

st.title("Trading Tool (DCA + Risiko + VIX Regime)")

# =========================
# SESSION STATE
# =========================
if "orders" not in st.session_state:
    st.session_state.orders = []

# =========================
# ORDERS
# =========================
st.subheader("📥 Orders")

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

st.write("---")
st.subheader("📊 Aktuelle Orders")

if st.session_state.orders:
    for i, o in enumerate(st.session_state.orders, 1):
        st.write(f"{i}. Preis: {o['price']} | Menge: {o['qty']}")
else:
    st.write("Keine Orders vorhanden")

# =========================
# CALCULATION
# =========================
if st.session_state.orders:

    total_qty = sum(o["qty"] for o in st.session_state.orders)
    total_cost = sum(o["price"] * o["qty"] for o in st.session_state.orders)
    avg_price = total_cost / total_qty

    st.write("---")
    st.subheader("📌 Position")

    st.write(f"Gesamtmenge: {total_qty}")
    st.write(f"Durchschnittspreis: {avg_price:.4f}")

    # =========================
    # MARKET INPUT
    # =========================
    market_price = st.number_input("Aktueller Marktpreis", value=18.0, step=0.01)
    direction = st.radio("Richtung", ["Long", "Short"])

    if direction == "Long":
        pnl = (market_price - avg_price) * total_qty
    else:
        pnl = (avg_price - market_price) * total_qty

    pnl_percent = (pnl / (avg_price * total_qty)) * 100

    st.subheader("💰 PnL")
    st.write(f"PnL: {pnl:.2f} €")
    st.write(f"PnL %: {pnl_percent:.2f} %")

    # =========================
    # RISK
    # =========================
    st.write("---")
    st.subheader("⚠️ Risiko")

    account_size = st.number_input("Kontogröße (€)", value=10000)
    stop_loss = st.number_input("Stop-Loss Preis", value=17.0, step=0.01)

    if direction == "Long":
        risk = (avg_price - stop_loss) * total_qty
    else:
        risk = (stop_loss - avg_price) * total_qty

    risk_percent = (risk / account_size) * 100

    st.write(f"Risiko bis Stop: {risk:.2f} €")
    st.write(f"Risiko vom Konto: {risk_percent:.2f} %")

    if risk_percent > 5:
        st.warning("⚠️ Risiko über 5%")

    # =========================
    # POSITION SIZE ALERT (BASE)
    # =========================
    st.write("---")
    st.subheader("📦 Positionskontrolle")

    if total_qty > 1000:
        st.error("⚠️ Über 1000 Stück Gesamtposition")
    else:
        st.success("Position im normalen Bereich")

    # =========================
    # REGIME SYSTEM
    # =========================
    st.write("---")
    st.subheader("📊 VIX Regime-System")

    vix = st.number_input("VIX Level", value=18.0, step=0.1)

    market_trend = st.selectbox(
        "Markttrend",
        ["Uptrend", "Sideways", "Downtrend"]
    )

    term_structure = st.selectbox(
        "VIX Struktur",
        ["Contango (normal)", "Flat", "Backwardation (Stress)"]
    )

    event_level = st.selectbox(
        "News-/Event-Level",
        ["Keine Events", "Makro-News", "Krisen-News (Banken/Krieg/Liquidität)"]
    )

    # =========================
    # SCORE CALCULATION
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
        "Krisen-News (Banken/Krieg/Liquidität)": 60
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
    st.subheader("🧠 Markt-Regime")

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
    # STRATEGY CONTROL
    # =========================
    st.subheader("⚙️ Strategie-Steuerung")

    if regime == "CALM":
        max_position_factor = 1.0
        allow_scaling = True

    elif regime == "NORMAL":
        max_position_factor = 0.8
        allow_scaling = True

    elif regime == "STRESS":
        max_position_factor = 0.5
        allow_scaling = False

    else:
        max_position_factor = 0.2
        allow_scaling = False

    adjusted_limit = 1000 * max_position_factor

    st.write(f"Max erlaubte Position: {adjusted_limit:.0f} Stück")

    if total_qty > adjusted_limit:
        st.error("⚠️ Positionslimit überschritten (Regime)")
    else:
        st.success("Position innerhalb Limit")

    if not allow_scaling:
        st.warning("⚠️ Skalierung aktuell deaktiviert im Regime")

    # =========================
    # RESET
    # =========================
    st.write("---")

    if st.button("Alles zurücksetzen"):
        st.session_state.orders = []
