from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AssetSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    ts_utc: datetime = Field(index=True)

    current_price: float
    ma_50: float
    swing_low: float

    current_volume: float
    avg_volume: float

    signal_below_ma_2: bool
    signal_break_swing_low_vol: bool
    signal_vix_jump_20: bool
    signal_macro_shock: bool

    exit_signal_count: int
    action: str


class RefreshRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts_utc: datetime = Field(index=True)
    macro_shock: bool
    status: str
    detail: str
