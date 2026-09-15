# Start the Traffic & Parking dashboard: launches the API + opens the browser.
# Usage:  .\start.ps1            (API on :8000, opens browser)
#         .\start.ps1 -NoBrowser (API only)   |   .\start.ps1 -Port 8001
param([switch]$NoBrowser, [int]$Port = 8000)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$PidFile = Join-Path $Root ".uvicorn.pid"

# 1) pick python: Mnemo venv -> python -> py launcher
$Py = "C:\Users\satvi\Desktop\Mnemo\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Py)) {
    $Py = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1).Source
}
if (-not $Py) {
    $pyLauncher = (Get-Command py -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    if (-not $pyLauncher) { Write-Error "No Python found. Install 3.11+ or edit `$Py in start.ps1." }
    & $pyLauncher -3 -c "import fastapi, uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Error "Python found but FastAPI/uvicorn missing. Run: pip install -r requirements.txt" }
    $Py = "$pyLauncher -3"
}

# 2) if our server is already running, just open the browser
if (Test-Path -LiteralPath $PidFile) {
    $old = Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue
    if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) {
        Write-Host "Server already running (PID $old). Opening browser..."
        if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$Port" }
        return
    }
}

# 3) launch uvicorn in its own window (logs visible), remember PID
Write-Host "Starting API from $Root ..."
$p = Start-Process -FilePath ($Py -split ' ')[0] `
    -ArgumentList ((($Py -split ' ')[1..9] + @("-m", "uvicorn", "backend.app:app", "--port", $Port)) -join ' ') `
    -WorkingDirectory $Root -PassThru
$p.Id | Set-Content -LiteralPath $PidFile
Start-Sleep -Seconds 4
if ($p.HasExited) { Write-Error "Server exited immediately. Run manually to see the error: $Py -m uvicorn backend.app:app --port $Port" }

Write-Host "API up (PID $($p.Id)). Dashboard: http://127.0.0.1:$Port"
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$Port" }
