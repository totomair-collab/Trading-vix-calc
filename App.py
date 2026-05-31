import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Event Engine Stable", layout="wide")

st.title("VIX Event-Driven Trading Engine (Stable)")

# =========================
# SESSION STATE INIT
# =========================
if "short_trades" not in st.session_state:
    st.session_state.short_trades = pd.DataFrame(columns=[
        "TradeID", "Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"
    ])

if "long_trades" not in st.session_state:
    st.session_state.long_trades = pd.DataFrame(columns=[
        "TradeID", "Entry_VIX", "Qty", "Direction", "Entry_Price", "Status"
    ])

# =========================
# INPUT
# =========================
vix = st.number_input("Current VIX", value=18.0, step=0.1)
prev_vix = st.number_input("Previous VIX", value=17.5, step=0.1)
equity = st.number_input("Capital (€)", value=10000)

unit_value = 100
spread = 0.13
max_notional = equity * 10

# =========================
# LADDERS
# =========================
st.subheader("📉 Short Ladder")

short_ladder = st.data_editor(
    pd.DataFrame({
        "Level": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
        "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic"
)

st.subheader("📈 Long Ladder")

long_ladder = st.data_editor(
    pd.DataFrame({
        "Level": [23, 24, 25, 26, 27, 28, 30],
        "Qty": [20, 40, 70, 100, 140, 180, 250]
    }),
    num_rows="dynamic"
)

# =========================
# EVENT DETECTION
# =========================
def crossed_up(level, prev, current):
    return prev < level <= current

# =========================
# TRADE CREATION (SAFE)
# =========================
def add_trade(store, level, qty, direction):
    trade_id = f"{direction}_{level}"

    if trade_id in store["TradeID"].values:
        return store

    new_trade = pd.DataFrame([{
        "TradeID": trade_id,
        "Entry_VIX": level,
        "Qty": qty,
        "Direction": direction,
        "Entry_Price": level,
        "Status": "OPEN"
    }])

    return pd.concat([store, new_trade], ignore_index=True)

# =========================
# APPLY EVENTS
# =========================
for _, row in short_ladder.iterrows():
    if crossed_up(row["Level"], prev_v
