import numpy as np
import pandas as pd


def clean_data(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["spx", "vix"])
    return df


def add_features(df):
    df = df.copy()

    df["spx_ma50"] = df["spx"].rolling(50).mean()
    df["drawdown"] = df["spx"] / df["spx"].cummax() - 1

    vix_mean = df["vix"].rolling(60).mean()
    vix_std = df["vix"].rolling(60).std()
    df["vix_z"] = (df["vix"] - vix_mean) / vix_std

    df["vix_mom_5d"] = df["vix"].pct_change(5)

    df["contango"] = 1.0
    return df


def set_regime(df):
    df = df.copy()

    short = (
        (df["vix"] < 15.5) &
        (df["vix_z"] < -0.6) &
        (df["spx"] > df["spx_ma50"])
    )

    transition = (
        (df["vix"] >= 15.5) &
        (df["vix"] <= 22)
    )

    long = (
        (df["vix"] > 22) &
        (df["drawdown"] < -0.05)
    )

    df["position"] = 0.0
    df.loc[short, "position"] = -1
    df.loc[transition, "position"] = 0.3
    df.loc[long, "position"] = 1

    df["position"] = df["position"].shift(1).fillna(0)

    return df


def vix_returns(df):
    df = df.copy()
    df["vix_ret"] = np.log(df["vix"] / df["vix"].shift(1))
    df["vix_ret"] = df["vix_ret"].fillna(0)
    return df


def backtest(df):
    df = df.copy()
    df["strategy_ret"] = df["position"] * df["vix_ret"]
    df["equity"] = (1 + df["strategy_ret"]).cumprod()
    return df


def stats(df):
    r = df["strategy_ret"]
    eq = df["equity"]

    return {
        "return": eq.iloc[-1] - 1,
        "max_dd": (eq / eq.cummax() - 1).min(),
        "sharpe": (r.mean() / (r.std() + 1e-9)) * np.sqrt(252)
    }


def run(df):
    df = clean_data(df)
    df = add_features(df)
    df = set_regime(df)
    df = vix_returns(df)
    df = backtest(df)
    return df, stats(df)


# -------------------------
# TEST RUN
# -------------------------

df = pd.read_csv("data.csv")

result, performance = run(df)

print(performance)
