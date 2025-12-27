from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class MarketDataClient:
    period: str = "6mo"
    interval: str = "1d"

    def history(self, symbol: str) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=self.period, interval=self.interval, auto_adjust=False)
        if df is None or df.empty:
            df = self._history_stooq(symbol)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.dropna(how="any")
        return df

    def _history_stooq(self, symbol: str) -> pd.DataFrame:
        s = symbol.strip()
        if s.startswith("^"):
            return pd.DataFrame()

        stooq_symbol = f"{s.lower()}.us"
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"

        try:
            raw = pd.read_csv(url)
        except Exception:
            return pd.DataFrame()

        if raw is None or raw.empty:
            return pd.DataFrame()

        expected = {"Date", "Open", "High", "Low", "Close"}
        if not expected.issubset(set(raw.columns)):
            return pd.DataFrame()

        raw["Date"] = pd.to_datetime(raw["Date"], errors="coerce")
        raw = raw.dropna(subset=["Date"])
        raw = raw.set_index("Date")

        if "Volume" not in raw.columns:
            raw["Volume"] = 0

        raw = raw[["Open", "High", "Low", "Close", "Volume"]]
        raw = raw.sort_index()
        return raw
