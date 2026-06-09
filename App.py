# ============================================================
# VIX REGIME SYSTEM - OPTIMIZED BACKTEST V1
# ============================================================

import numpy as np
import pandas as pd

# ------------------------------------------------------------
# 1. FEATURE ENGINEERING
# ------------------------------------------------------------

def add_features(df):

    df = df.copy()

    # Returns
    df["spx_ret"] = df["spx"].pct_change()

    # Trend
    df["spx_ma50"] = df["spx"].rolling(50).mean()

    # Drawdown
    df["drawdown"] = df["spx"] / df["spx"].cummax() - 1

    # VIX Z-Score (60d)
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


# ------------------------------------------------------------
# 2. REGIME MODEL (OPTIMIZED THRESHOLDS)
# ------------------------------------------------------------

def classify_regime(row,
                    vix_low=15.5,
                    vix_high=22,
                    contango_min=1.015):

    vix = row["vix"]
    vix_z = row["vix_z"]
    spx = row["spx"]
    ma50 = row["spx_ma50"]
    drawdown = row["drawdown"]
    contango = row["contango"]
    vix_mom = row["vix_mom_5d"]

    # -----------------------------
    # SHORT VOL (CARRY ZONE)
    # -----------------------------
    if (
        vix < vix_low and
        vix_z < -0.6 and
        spx > ma50 and
        contango > contango_min
    ):
        return -1.0

    # -----------------------------
    # TRANSITION (EARLY STRESS)
    # -----------------------------
    elif (
        vix_low <= vix <= vix_high and
        vix_mom > 0.08
    ):
        return 0.3

    # -----------------------------
    # LONG VOL (STRESS)
    # -----------------------------
    elif (
        vix > vix_high and
        drawdown < -0.05
    ):
        return 1.0

    # -----------------------------
    # PANIC REDUCTION ZONE
    # -----------------------------
    elif vix > 30:
        return 0.5

    return 0.0


# ------------------------------------------------------------
# 3. SIGNAL ENGINE
# ------------------------------------------------------------

def generate_signals(df, params):

    df = df.copy()

    df["position"] = df.apply(
        lambda row: classify_regime(
            row,
            params["vix_low"],
            params["vix_high"],
            params["contango_min"]
        ),
        axis=1
    )

    # avoid lookahead bias
    df["position"] = df["position"].shift(1).fillna(0)

    return df


# ------------------------------------------------------------
# 4. VIX RETURN MODEL (ASYMMETRIC)
# ------------------------------------------------------------

def vix_returns(df):

    df = df.copy()

    df["vix_ret"] = np.log(df["vix
