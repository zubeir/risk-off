from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import select

from app.market_data import MarketDataClient
from app.models import AssetSnapshot, RefreshRun
from app.signals import compute_action, compute_asset_signals, compute_vix_jump_20


def run_refresh(*, engine, assets: list[str], index_symbol: str, vix_symbol: str, high_beta_assets: set[str], macro_shock: bool) -> RefreshRun:
    ts = datetime.now(timezone.utc)
    client = MarketDataClient()

    run = RefreshRun(ts_utc=ts, macro_shock=macro_shock, status="started", detail="")

    with engine.begin() as conn:
        pass

    from app.db import get_session

    with get_session(engine) as session:
        session.add(run)
        session.commit()
        session.refresh(run)

        try:
            vix_df = client.history(vix_symbol)
            vix_jump = compute_vix_jump_20(vix_df)

            symbols = [index_symbol] + assets

            skipped: list[str] = []

            for symbol in symbols:
                df = client.history(symbol)
                if df.empty:
                    skipped.append(f"{symbol}: no data")
                    continue
                try:
                    cs = compute_asset_signals(df)
                except Exception as e:
                    skipped.append(f"{symbol}: {e}")
                    continue

                signal_vix_jump_20 = bool(vix_jump and symbol == index_symbol)

                signal_count = int(cs.signal_below_ma_2) + int(cs.signal_break_swing_low_vol) + int(signal_vix_jump_20) + int(macro_shock)

                action = compute_action(symbol, signal_count, high_beta_assets)

                snapshot = AssetSnapshot(
                    symbol=symbol,
                    ts_utc=ts,
                    current_price=cs.current_price,
                    ma_50=cs.ma_50,
                    swing_low=cs.swing_low,
                    current_volume=cs.current_volume,
                    avg_volume=cs.avg_volume,
                    signal_below_ma_2=cs.signal_below_ma_2,
                    signal_break_swing_low_vol=cs.signal_break_swing_low_vol,
                    signal_vix_jump_20=signal_vix_jump_20,
                    signal_macro_shock=macro_shock,
                    exit_signal_count=signal_count,
                    action=action,
                )

                session.add(snapshot)

            run.status = "success"
            run.detail = "ok" if not skipped else ("skipped: " + "; ".join(skipped))
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
        except Exception as e:
            run.status = "error"
            run.detail = str(e)
            session.add(run)
            session.commit()
            session.refresh(run)
            return run


def get_latest_snapshots(*, engine) -> list[AssetSnapshot]:
    from app.db import get_session

    with get_session(engine) as session:
        latest_ts = session.exec(select(AssetSnapshot.ts_utc).order_by(AssetSnapshot.ts_utc.desc())).first()
        if latest_ts is None:
            return []
        rows = session.exec(select(AssetSnapshot).where(AssetSnapshot.ts_utc == latest_ts).order_by(AssetSnapshot.symbol.asc())).all()
        return list(rows)


def get_snapshots_since(*, engine, since_utc: datetime) -> list[AssetSnapshot]:
    from app.db import get_session

    with get_session(engine) as session:
        rows = session.exec(
            select(AssetSnapshot)
            .where(AssetSnapshot.ts_utc >= since_utc)
            .order_by(AssetSnapshot.ts_utc.desc(), AssetSnapshot.symbol.asc())
        ).all()
        return list(rows)
