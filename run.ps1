$ErrorActionPreference = 'Stop'

param(
  [int]$Port = 8000
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root '.venv'
$python = Join-Path $venv 'Scripts\python.exe'

function Stop-PortProcess {
  param([int]$Port)

  $pids = @()
  try {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction Stop
    foreach ($c in $conns) {
      if ($c.OwningProcess -and ($pids -notcontains $c.OwningProcess)) {
        $pids += $c.OwningProcess
      }
    }
  } catch {
    return
  }

  foreach ($pid in $pids) {
    try {
      Write-Host "Stopping PID $pid on port $Port" -ForegroundColor Yellow
      Stop-Process -Id $pid -Force -ErrorAction Stop
    } catch {
      Write-Host "Failed to stop PID $pid: $($_.Exception.Message)" -ForegroundColor Red
    }
  }
}

Stop-PortProcess -Port $Port

if (!(Test-Path $python)) {
  python -m venv $venv
}

& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $root 'requirements.txt')

& $python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
