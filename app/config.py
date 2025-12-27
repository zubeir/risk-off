from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value is not None and value.strip() != "" else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    assets: list[str]
    index_symbol: str
    vix_symbol: str
    high_beta_assets: set[str]
    refresh_hours: int
    sqlite_path: str


def get_settings() -> Settings:
    assets = _csv(
        _env(
            "ASSETS",
            "JETS,AWAY,SPY,"
            "XLB,XLC,XLE,XLF,XLI,XLK,XLP,XLU,XLV,XLY,XLRE",
        )
    )
    return Settings(
        assets=assets,
        index_symbol=_env("INDEX_SYMBOL", "SPY"),
        vix_symbol=_env("VIX_SYMBOL", "VIXY"),
        high_beta_assets=set(_csv(_env("HIGH_BETA_ASSETS", "SPY,QQQ,IWM,XLK,XLY,XLC"))),
        refresh_hours=_env_int("REFRESH_HOURS", 4),
        sqlite_path=_env("SQLITE_PATH", "risk_off.db"),
    )
