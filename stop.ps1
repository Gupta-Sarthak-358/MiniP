# Stop the dashboard API started by start.ps1.
$ErrorActionPreference = "SilentlyContinue"
$PidFile = Join-Path $PSScriptRoot ".uvicorn.pid"
$stopped = $false

if (Test-Path -LiteralPath $PidFile) {
    $pid_ = Get-Content -LiteralPath $PidFile
    if ($pid_ -and (Get-Process -Id $pid_ -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $pid_ -Force
        Write-Host "Stopped server (PID $pid_)."
        $stopped = $true
    }
    Remove-Item -LiteralPath $PidFile -Force
}
if (-not $stopped) {
    # fallback: any uvicorn serving our app
    $found = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" |
        Where-Object { $_.CommandLine -match 'uvicorn backend\.app:app' }
    foreach ($pr in $found) {
        Stop-Process -Id $pr.ProcessId -Force
        Write-Host "Stopped server (PID $($pr.ProcessId))."
        $stopped = $true
    }
}
if (-not $stopped) { Write-Host "No running dashboard server found." }
