from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ComputedSignals:
    current_price: float
    ma_50: float
    swing_low: float
    current_volume: float
    avg_volume: float

    signal_below_ma_2: bool
    signal_break_swing_low_vol: bool


def compute_asset_signals(df: pd.DataFrame) -> ComputedSignals:
    if df.empty or len(df) < 60:
        raise ValueError("Not enough historical bars to compute signals")

    close = df["Close"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float)

    current_price = float(close.iloc[-1])
    ma_50 = float(close.rolling(50).mean().iloc[-1])

    close_last2 = close.iloc[-2:]
    ma_last2 = close.rolling(50).mean().iloc[-2:]
    signal_below_ma_2 = bool((close_last2 < ma_last2).all())

    swing_window = 20
    if len(low) <= swing_window + 2:
        swing_low = float(low.min())
    else:
        swing_low = float(low.iloc[-(swing_window + 2) : -2].min())

    avg_window = 20
    avg_volume = float(vol.rolling(avg_window).mean().iloc[-1])
    current_volume = float(vol.iloc[-1])

    signal_break_swing_low_vol = bool((current_price < swing_low) and (current_volume > avg_volume))

    return ComputedSignals(
        current_price=current_price,
        ma_50=ma_50,
        swing_low=swing_low,
        current_volume=current_volume,
        avg_volume=avg_volume,
        signal_below_ma_2=signal_below_ma_2,
        signal_break_swing_low_vol=signal_break_swing_low_vol,
    )


def compute_vix_jump_20(vix_df: pd.DataFrame) -> bool:
    if vix_df.empty or len(vix_df) < 10:
        return False
    close = vix_df["Close"].astype(float)
    current = float(close.iloc[-1])
    prev3 = float(close.iloc[-4])
    if prev3 <= 0:
        return False
    return bool((current / prev3 - 1.0) > 0.2)


def compute_action(symbol: str, signal_count: int, high_beta_assets: set[str]) -> str:
    if signal_count <= 0:
        return "Hold"
    if signal_count == 1:
        return "Tighten Stops" if symbol in high_beta_assets else "Hold"
    return "Exit"
