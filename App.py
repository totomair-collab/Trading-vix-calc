
import streamlit as st

st.title("DCA Rechner")

if "orders" not in st.session_state:
    st.session_state.orders = []

price = st.number_input("Preis", value=18.0)
qty = st.number_input("Menge", value=100)

if st.button("Order hinzufügen"):
    st.session_state.orders.append({"price": price, "qty": qty})

st.write("Orders:", st.session_state.orders)

if st.session_state.orders:
    total_qty = sum(o["qty"] for o in st.session_state.orders)
    total_cost = sum(o["price"] * o["qty"] for o in st.session_state.orders)
    avg = total_cost / total_qty

    st.write("Avg Price:", avg)
