import streamlit as st
import pandas as pd

st.set_page_config(page_title="VIX Quant Framework", layout="wide")
st.title("VIX Quant Risk Framework")

# =========================
# STATE
# =========================
if "short_trades" not in st.session_state:
    st.session_state.short_trades = pd.DataFrame(columns=[
        "TradeID", "Entry", "Qty", "Side", "Status"
    ])

if "long_trades" not in st.session_state:
    st.session_state.long_trades = pd.DataFrame(columns=[
        "TradeID", "Entry", "Qty", "Side", "Status"
    ])

if "last_regime" not in st.session_state:
    st.session_state.last_regime = None

if "equity_curve" not in st.session_state:
    st.session_state.equity_curve = []

# =========================
# INPUT
# =========================
vix = st.number_input("VIX", value=18.0)
prev_vix = st.number_input("Prev VIX", value=17.5)
equity = st.number_input("Equity (€)", value=10000)

# =========================
# REGIME
# =========================
def regime(v):
    if v < 20:
        return 1
    elif v < 27:
        return 2
    return 3

reg = regime(vix)

# Leverage mapping
leverage_map = {
    1: 10,
    2: 6,
    3: 3
}

max_leverage = leverage_map[reg]
max_exposure = equity * max_leverage

# =========================
# LADDERS
# =========================
short_ladder = st.data_editor(pd.DataFrame({
    "Level": [17.25, 17.35, 17.5, 17.7, 17.95, 18.25, 18.6, 19.0, 19.5],
    "Qty": [20, 25, 35, 50, 70, 95, 130, 180, 250]
}), num_rows="dynamic")

long_ladder = st.data_editor(pd.DataFrame({
    "Level": [23, 24, 25, 26, 27, 28, 30],
    "Qty": [20, 40, 70, 100, 140, 180, 250]
}), num_rows="dynamic")

# =========================
# CORE FUNCTIONS
# =========================
def crossed(level, prev, current):
    return prev < level <= current


def add_trade(df, level, qty, side):
    trade_id = f"{side}_{level}"

    if trade_id in df["TradeID"].values:
        return df

    row = pd.DataFrame([{
        "TradeID": trade_id,
        "Entry": level,
        "Qty": qty,
        "Side": side,
        "Status": "OPEN"
    }])

    return pd.concat([df, row], ignore_index=True)


def apply_events(ladder, prev, current, side, df):
    for _, r in ladder.iterrows():
        if crossed(r["Level"], prev, current):
            df = add_trade(df, r["Level"], r["Qty"], side)
    return df


def apply_exit(df, vix):
    df = df.copy()
    for i in range(len(df)):
        if df.loc[i, "Side"] == "SHORT" and vix >= 20:
            df.loc[i, "Status"] = "CLOSED"
        if df.loc[i, "Side"] == "LONG" and vix < 23:
            df.loc[i, "Status"] = "CLOSED"
    return df


def exposure(df, side):
    df = df[df["Status"] == "OPEN"]
    return (df["Entry"] * df["Qty"]).sum() if len(df) > 0 else 0


def pnl(df, vix):
    df = df[df["Status"] == "CLOSED"]
    total = 0

    for _, t in df.iterrows():
        diff = (vix - t["Entry"]) if t["Side"] == "LONG" else (t["Entry"] - vix)
        total += diff * t["Qty"]

    return total

# =========================
# REGIME ROTATION ENGINE
# =========================
def rotate(old, new, short_df, long_df):
    if old is None:
        return short_df, long_df

    # risk-off in high vol
    if old < new:
        short_df.loc[:, "Qty"] *= 0.7

    # risk-on in calm markets
    if old > new:
        long_df.loc[:, "Qty"] *= 0.7

    # extreme regimes
    if new == 3:
        short_df.loc[:, "Status"] = "CLOSED"
    if new == 1:
        long_df.loc[:, "Status"] = "CLOSED"

    return short_df, long_df

# =========================
# EXECUTION
# =========================
st.session_state.short_trades = apply_events(short_ladder, prev_vix, vix, "SHORT", st.session_state.short_trades)
st.session_state.long_trades = apply_events(long_ladder, prev_vix, vix, "LONG", st.session_state.long_trades)

st.session_state.short_trades = apply_exit(st.session_state.short_trades, vix)
st.session_state.long_trades = apply_exit(st.session_state.long_trades, vix)

st.session_state.short_trades, st.session_state.long_trades = rotate(
    st.session_state.last_regime,
    reg,
    st.session_state.short_trades,
    st.session_state.long_trades
)

st.session_state.last_regime = reg

# =========================
# RISK ENGINE
# =========================
long_exp = exposure(st.session_state.long_trades, "LONG")
short_exp = exposure(st.session_state.short_trades, "SHORT")

net_exposure = long_exp - short_exp

if abs(net_exposure) > max_exposure:
    scale = max_exposure / abs(net_exposure)
    net_exposure *= scale

net_pnl = pnl(st.session_state.long_trades, vix) + pnl(st.session_state.short_trades, vix)

# drawdown protection
st.session_state.equity_curve.append(net_pnl)

drawdown = min(st.session_state.equity_curve[-50:]) if len(st.session_state.equity_curve) > 10 else 0

# =========================
# OUTPUT
# =========================
st.subheader("Regime")
st.write(reg)

st.subheader("Exposure")
st.write(net_exposure)

st.subheader("PnL")
st.write(net_pnl)

st.subheader("Drawdown")
st.write(drawdown)

st.subheader("Short Trades")
st.dataframe(st.session_state.short_trades)

st.subheader("Long Trades")
st.dataframe(st.session_state.long_trades)
