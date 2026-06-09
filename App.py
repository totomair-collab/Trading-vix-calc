import numpy as np
import pandas as pd


# ============================================================
# 1. CLEAN DATA
# ============================================================

def clean_data(df):
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["spx", "vix"])
    return df


# ============================================================
# 2. FEATURES
# ============================================================

def add_features(df):
    df = df.copy()

    df["spx_ret"] = df["spx"].pct_change()
    df["spx_ma50"] = df["spx"].rolling(50).mean()
    df["drawdown"] = df["spx"] / df["spx"].cummax() - 1

    vix_mean = df["vix"].rolling(60).mean()
    vix_std = df["vix"].rolling(60).std()
    df["vix_z"] = (df["vix"] - vix_mean) / vix_std

    df["vix_mom_5d"] = df["vix"].pct_change(5)

    if "f1" in df.columns and "f2" in df.columns:
        df["contango"] = df["f2"] / df["f1"]
    else:
        df["contango"] = 1.0

    return df


# ============================================================
# 3. REGIME
# ============================================================

def set_regime(df):
    df = df.copy()

    short_vol = (
        (df["vix"] < 15.5) &
        (df["vix_z"] < -0.6) &
        (df["spx"] > df["spx_ma50"]) &
        (df["contango"] > 1.015)
    )

    transition = (
        (df["vix"] >= 15.5) &
        (df["vix"] <= 22) &
        (df["vix_mom_5d"] > 0.08)
    )

    long_vol = (
        (df["vix"] > 22) &
        (df["drawdown"] < -0.05)
    )

    panic = (df["vix"] > 30)

    df["position"] = 0.0
    df.loc[short_vol, "position"] = -1.0
    df.loc[transition, "position"] = 0.3
    df.loc[long_vol, "position"] = 1.0
    df.loc[panic, "position"] = 0.5

    df["position"] = df["position"].shift(1).fillna(0)

    return df


# ============================================================
# 4. RETURNS
# ============================================================

def vix_returns(df):
    df = df.copy()

    df["vix_ret"] = np.log(df["vix"] / df["vix"].shift(1))

    vol_mean = df["vix"].rolling(20).mean()

    df.loc[df["vix"] > vol_mean, "vix_ret"] *= 1.6

    df["vix_ret"] = df["vix_ret"].fillna(0)

    return df


# ============================================================
# 5. BACKTEST
# ============================================================

def backtest(df):
    df = df.copy()

    df["strategy_ret"] = df["position"] * df["vix_ret"]
    df["equity"] = (1 + df["strategy_ret"]).cumprod()

    return df


# ============================================================
# 6. STATS
# ============================================================

def stats(df):
    r = df["strategy_ret"].fillna(0)
    eq = df["equity"]

    return {
        "return": float(eq.iloc[-1] - 1),
        "max_dd": float((eq / eq.cummax() - 1).min()),
        "sharpe": float((r.mean() / (r.std() + 1e-9)) * np.sqrt(252))
    }


# ============================================================
# 7. PIPELINE
# ============================================================

def run(df):
    df = clean_data(df)
    df = add_features(df)
    df = set_regime(df)
    df = vix_returns(df)
    df = backtest(df)

    return df, stats(df)


# ============================================================
# USAGE
# ============================================================

"""
import pandas as pd

df = pd.read_csv("data.csv")

result, performance = run(df)

print(performance)
"""
