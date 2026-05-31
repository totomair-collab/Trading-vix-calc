import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Trading Engine", layout="wide")

st.title("VIX Event Engine – Full Stable Version")

# =========================
# SESSION STATE
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
# INPUTS (WICHTIG: ZEIT WIEDER DRIN)
# =========================
vix = st.number_input("Aktueller VIX", value=18.0, step=0.1)
prev_vix = st.number_input("Vorheriger VIX", value=17.5, step=0.1)

session_hours = st.number_input("Session Dauer (Stunden)", value=1.0, step=0.5)

equity = st.number_input("Kapital (€)", value=10000)

unit_value = 100
spread = 0.13
max_notional = equity * 10

# =========================
# LADDERS (MIT NAMEN WIEDER SAUBER)
# =========================
st.subheader("Short Entry Tabelle")

short_ladder = st.data_editor(
    pd.DataFrame({
        "VIX_Level": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
        "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
    }),
    num_rows="dynamic",
    key="short_table"
)

st.subheader("Long Entry Tabelle")

long_ladder = st.data_editor(
    pd.DataFrame({
        "VIX_Level": [23, 24, 25, 26, 27, 28, 30],
        "Qty": [20, 40, 70, 100, 140, 180, 250]
    }),
    num_rows="dynamic",
    key="long_table"
)

# =========================
# LOGIC
# =========================
def crossed(level, prev, current):
    return prev < level <= current


def add_trade(store, level, qty, direction):
    trade_id = f"{direction}_{level}"

    if trade_id in store["TradeID"].values:
        return store

    new_row = pd.DataFrame([{
        "TradeID": trade_id,
        "Entry_VIX": level,
        "Qty": qty,
        "Direction": direction,
        "Entry_Price": level,
        "Status": "OPEN"
    }])

    return pd.concat([store, new_row], ignore_index=True)


def apply_events(ladder, prev, current, direction, store):
    if ladder is None or len(ladder) == 0:
        return store

    for i in range(len(ladder)):
        level = ladder.iloc[i]["VIX_Level"]
        qty = ladder.iloc[i]["Qty"]

        if crossed(level, prev, current):
            store = add_trade(store, level, qty, direction)

    return store


def apply_exit(df, vix):
    if df is None or len(df) == 0:
        return df

    df = df.copy()

    for i in range(len(df)):
        if df.loc[i, "Direction"] == "SHORT":
            if vix >= 20:
                df.loc[i, "Status"] = "CLOSED"

        if df.loc[i, "Direction"] == "LONG":
            if vix < 23:
                df.loc[i, "Status"] = "CLOSED"

    return df


def open_qty(df):
    if df is None or len(df) == 0:
        return 0
    return df[df["Status"] == "OPEN"]["Qty"].sum()


def pnl(df, vix):
    if df is None or len(df) == 0:
        return 0

    total = 0

    for _, t in df.iterrows():
        if t["Status"] != "CLOSED":
            continue

        entry = t["Entry_Price"]
        qty = t["Qty"]

        if t["Direction"] == "SHORT":
            total += (entry - vix) * qty * 0.01
        else:
            total += (vix - entry) * qty * 0.01

    return total


# =========================
# ENGINE EXECUTION (STABIL)
# =========================
st.session_state.short_trades = apply_events(
    short_ladder,
    prev_vix,
    vix,
    "SHORT",
    st.session_state.short_trades
)

st.session_state.long_trades = apply_events(
    long_ladder,
    prev_vix,
    vix,
    "LONG",
    st.session_state.long_trades
)

st.session_state.short_trades = apply_exit(st.session_state.short_trades, vix)
st.session_state.long_trades = apply_exit(st.session_state.long_trades, vix)

# =========================
# METRICS
# =========================
short_qty = open_qty(st.session_state.short_trades)
long_qty = open_qty(st.session_state.long_trades)

net_exposure = (long_qty - short_qty) * unit_value

spread_costs = (
    len(st.session_state.short_trades)
    + len(st.session_state.long_trades)
) * spread

net_pnl = pnl(st.session_state.short_trades, vix) + pnl(st.session_state.long_trades, vix) - spread_costs

# =========================
# RISK CAP
# =========================
if abs(net_exposure) > max_notional:
    net_exposure = max_notional * (1 if net_exposure > 0 else -1)

# =========================
# OUTPUT
# =========================
st.subheader("📊 Session Daten")

st.write(f"Session Dauer: {session_hours} Stunden")
st.write(f"VIX: {vix}")
st.write(f"Vorheriger VIX: {prev_vix}")

st.subheader("Exposure")
st.write(net_exposure)

st.subheader("PnL")
st.write(net_pnl)
st.write(spread_costs)

st.subheader("Short Trades Tabelle")
st.dataframe(st.session_state.short_trades)

st.subheader("Long Trades Tabelle")
st.dataframe(st.session_state.long_trades)
