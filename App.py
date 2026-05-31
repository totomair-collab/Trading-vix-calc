import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Full Quant System", layout="wide")
st.title("VIX Full Portfolio + Backtest + Journal System")

# =========================
# STATE
# =========================
if "positions" not in st.session_state:
    st.session_state.positions = []

if "journal" not in st.session_state:
    st.session_state.journal = []

if "equity_curve" not in st.session_state:
    st.session_state.equity_curve = []

# =========================
# INPUT
# =========================
st.sidebar.header("Simulation Settings")

initial_equity = st.sidebar.number_input("Initial Equity", value=10000)
time_step = st.sidebar.number_input("Time Step (days)", value=1)

vix_series = st.data_editor(
    pd.DataFrame({
        "Day": list(range(1, 12)),
        "VIX": [17.2, 17.5, 17.8, 18.2, 18.6, 19.1, 19.6, 20.2, 21.5, 23.0, 25.0]
    }),
    num_rows="dynamic",
    key="series"
)

# =========================
# REGIME
# =========================
def regime(v):
    if v < 20:
        return 1
    elif v < 27:
        return 2
    return 3

leverage_map = {1: 10, 2: 6, 3: 3}

# =========================
# TABLES (ENTRY STRUCTURE)
# =========================
short_table = pd.DataFrame({
    "Level": [17.25, 17.5, 18.0, 18.5, 19.0],
    "Qty":   [20, 35, 50, 80, 120]
})

long_table = pd.DataFrame({
    "Level": [23, 24, 25, 26, 27],
    "Qty":   [30, 60, 100, 140, 200]
})

st.subheader("Short Entry Table")
st.dataframe(short_table)

st.subheader("Long Entry Table")
st.dataframe(long_table)

# =========================
# CORE FUNCTIONS
# =========================
def add_position(side, entry, qty, day):
    st.session_state.positions.append({
        "side": side,
        "entry": entry,
        "qty": qty,
        "day": day,
        "status": "OPEN"
    })

    st.session_state.journal.append({
        "event": "ENTRY",
        "side": side,
        "entry": entry,
        "qty": qty,
        "day": day
    })


def close_positions(side, day, vix):
    for p in st.session_state.positions:
        if p["side"] == side and p["status"] == "OPEN":
            p["status"] = "CLOSED"

            pnl = (vix - p["entry"]) * p["qty"] if side == "LONG" else (p["entry"] - vix) * p["qty"]

            st.session_state.journal.append({
                "event": "EXIT",
                "side": side,
                "entry": p["entry"],
                "exit": vix,
                "qty": p["qty"],
                "pnl": pnl,
                "day": day
            })


def mark_to_market(vix):
    pnl = 0
    exposure = 0

    for p in st.session_state.positions:
        if p["status"] != "OPEN":
            continue

        if p["side"] == "LONG":
            pnl += (vix - p["entry"]) * p["qty"]
            exposure += p["entry"] * p["qty"]
        else:
            pnl += (p["entry"] - vix) * p["qty"]
            exposure -= p["entry"] * p["qty"]

    return pnl, exposure

# =========================
# BACKTEST LOOP
# =========================
prev_vix = None

for _, row in vix_series.iterrows():
    vix = row["VIX"]
    day = row["Day"]
    reg = regime(vix)

    if prev_vix is not None:

        # ENTRY LOGIC
        for _, r in short_table.iterrows():
            if prev_vix < r["Level"] <= vix:
                add_position("SHORT", r["Level"], r["Qty"], day)

        for _, r in long_table.iterrows():
            if prev_vix < r["Level"] <= vix:
                add_position("LONG", r["Level"], r["Qty"], day)

        # EXIT LOGIC (REGIME BASED)
        if reg == 3:
            close_positions("SHORT", day, vix)

        if reg == 1:
            close_positions("LONG", day, vix)

    pnl, exposure = mark_to_market(vix)

    st.session_state.equity_curve.append(initial_equity + pnl)

    prev_vix = vix

# =========================
# RESULTS
# =========================
positions_df = pd.DataFrame(st.session_state.positions)
journal_df = pd.DataFrame(st.session_state.journal)

final_equity = st.session_state.equity_curve[-1]
max_dd = min(st.session_state.equity_curve)

# =========================
# OUTPUT
# =========================
st.subheader("Final Equity")
st.write(final_equity)

st.subheader("Equity Curve")
st.write(st.session_state.equity_curve)

st.subheader("Max Drawdown")
st.write(max_dd)

st.subheader("Positions")
st.dataframe(positions_df)

st.subheader("Trade Journal (Training Diary)")
st.dataframe(journal_df)
