import numpy as np
import pandas as pd


# ============================================================
# 1. CLEANING / SAFETY LAYER
# ============================================================

def clean_data(df):
    df = df.copy()

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["spx", "vix"])

    return df


# ============================================================
# 2. FEATURE ENGINE (VECTORIZED)
# ============================================================

def add_features(df):
    df = df.copy()

    # Returns
    df["spx_ret"] = df["spx"].pct_change()

    # Trend
    df["spx_ma50"] = df["spx"].rolling(50).mean()

    # Drawdown
    df["drawdown"] = df["spx"] / df["spx"].cummax() - 1

    # VIX Z-Score
    vix_mean = df["vix"].rolling(60).mean()
    vix_std = df["vix"].rolling(60).std()

    df["vix_z"] = (df["vix"] - vix_mean) / vix_std

    # Momentum
    df["vix_mom_5d"] = df["vix"].pct_change(5)

    # Contango fallback
    if "f1" in df.columns and "f2" in df.columns:
        df["contango"] = df["f2"] / df["f1"]
    else:
        df["contango"] = 1.0

    return df


# ============================================================
# 3. REGIME ENGINE (FULLY VECTORIZED)
# ============================================================

def compute_regime(df,
                   vix_low=15.5,
                   vix_high=22,
                   contango_min=1.015):

    df = df.copy()

    vix = df["vix"]
    vix_z = df["vix_z"]
    spx = df["spx"]
    ma50 = df["spx_ma50"]
    drawdown = df["drawdown"]
    contango = df["contango"]
    vix_mom = df["vix_mom_5d"]

    short_vol = (
        (vix < vix_low) &
        (vix_z < -0.6) &
        (spx > ma50
