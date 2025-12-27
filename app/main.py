from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.db import create_db_engine, init_db
from app.models import RefreshRun
from app.refresh import get_latest_snapshots, get_snapshots_since, run_refresh

load_dotenv()

settings = get_settings()
engine = create_db_engine(settings.sqlite_path)

app = FastAPI(title="Risk-Off Dashboard")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

scheduler = BackgroundScheduler(daemon=True)


def _job_refresh() -> None:
    run_refresh(
        engine=engine,
        assets=settings.assets,
        index_symbol=settings.index_symbol,
        vix_symbol=settings.vix_symbol,
        high_beta_assets=settings.high_beta_assets,
        macro_shock=False,
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db(engine)

    if not scheduler.running:
        scheduler.add_job(_job_refresh, "interval", hours=settings.refresh_hours, id="refresh_job", replace_existing=True)
        scheduler.start()

    _job_refresh()


@app.on_event("shutdown")
def on_shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, action: str | None = None, sort: str = "action"):
    rows = get_latest_snapshots(engine=engine)

    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo

    since = datetime.now(timezone.utc) - timedelta(days=4)
    history_rows = get_snapshots_since(engine=engine, since_utc=since)

    if action:
        rows = [r for r in rows if r.action == action]

    def action_rank(a: str) -> int:
        if a == "Exit":
            return 0
        if a == "Tighten Stops":
            return 1
        return 2

    if sort == "signals":
        rows = sorted(rows, key=lambda r: (-r.exit_signal_count, r.symbol))
    elif sort == "symbol":
        rows = sorted(rows, key=lambda r: r.symbol)
    else:
        rows = sorted(rows, key=lambda r: (action_rank(r.action), -r.exit_signal_count, r.symbol))

    # convert last timestamp to Eastern Time (EST/EDT) for display
    if rows:
        last_ts = rows[0].ts_utc.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M %p")
    else:
        last_ts = None

    from sqlmodel import select
    from app.db import get_session

    last_status = None
    last_detail = None
    with get_session(engine) as session:
        rr = session.exec(select(RefreshRun).order_by(RefreshRun.ts_utc.desc())).first()
        if rr:
            last_status = rr.status
            last_detail = rr.detail

    # add formatted EST timestamps to history rows for display
    for h in history_rows:
        try:
            h.ts_est = h.ts_utc.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            h.ts_est = None

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rows": rows,
            "history_rows": history_rows,
            "last_ts": last_ts,
            "action_filter": action or "",
            "sort": sort,
            "last_status": last_status,
            "last_detail": last_detail,
        },
    )


@app.get("/api/status")
def api_status():
    rows = get_latest_snapshots(engine=engine)
    from zoneinfo import ZoneInfo

    ts_est = None
    if rows:
        try:
            ts_est = rows[0].ts_utc.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            ts_est = None

    payload = {
        "ts_utc": rows[0].ts_utc.isoformat() if rows else None,
        "ts_est": ts_est,
        "rows": [r.model_dump() for r in rows],
    }
    return JSONResponse(content=jsonable_encoder(payload))


@app.post("/api/refresh")
def api_refresh(macro_shock: bool = False):
    rr = run_refresh(
        engine=engine,
        assets=settings.assets,
        index_symbol=settings.index_symbol,
        vix_symbol=settings.vix_symbol,
        high_beta_assets=settings.high_beta_assets,
        macro_shock=macro_shock,
    )
    return JSONResponse(content=jsonable_encoder(rr.model_dump()))
