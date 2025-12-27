# Risk-Off Dashboard Agent

## What this is
A small FastAPI service that periodically fetches market data and computes “risk-off” signals for:

- S&P 500 index (default: `^GSPC`)
- VIX (default: `^VIX`)
- 10 user-selected tickers

It stores snapshots in SQLite and serves a simple dashboard UI.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configure

Create a `.env` file (optional):

```env
ASSETS=JETS,AWAY,SPY,XLB,XLC,XLE,XLF,XLI,XLK,XLP,XLU,XLV,XLY,XLRE
INDEX_SYMBOL=SPY
VIX_SYMBOL=VIXY
HIGH_BETA_ASSETS=SPY,QQQ,IWM,XLK,XLY,XLC,JETS,AWAY
REFRESH_HOURS=4
SQLITE_PATH=risk_off.db
```

## Run

### Option A: run script (recommended)

PowerShell:

```powershell
./run.ps1
```

Command Prompt:

```bat
run.bat
```

### Option B: manual

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/`

### If you see "[winerror 10048]" (port 8000 already in use)

That means another process is already using port `8000`.

- Stop the other server process, then re-run `run.ps1` / `run.bat`.
- Or run uvicorn on a different port (example below):

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## Notes

- Data source defaults to `yfinance` (no API key).
- “Macro shock” is currently a manual flag you can set per refresh call.
