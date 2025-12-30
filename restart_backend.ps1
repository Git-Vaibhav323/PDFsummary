# Script to stop any existing backend processes and restart the backend

Write-Host "Checking for processes on port 8000..." -ForegroundColor Yellow

# Find processes using port 8000
$port8000 = netstat -ano | findstr :8000 | Select-String "LISTENING"
if ($port8000) {
    $pid = ($port8000 -split '\s+')[-1]
    Write-Host "Found process $pid using port 8000. Stopping..." -ForegroundColor Yellow
    try {
        Stop-Process -Id $pid -Force -ErrorAction Stop
        Start-Sleep -Seconds 2
        Write-Host "Process stopped successfully." -ForegroundColor Green
    } catch {
        Write-Host "Could not stop process. Trying taskkill..." -ForegroundColor Yellow
        taskkill /F /PID $pid 2>$null
    }
} else {
    Write-Host "No process found on port 8000." -ForegroundColor Green
}

# Also check for Python processes that might be running the backend
Write-Host "`nChecking for Python processes..." -ForegroundColor Yellow
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "Found $($pythonProcs.Count) Python process(es)." -ForegroundColor Yellow
    Write-Host "If one of these is your backend, stop it manually (Ctrl+C in that terminal)." -ForegroundColor Yellow
}

Write-Host "`nPort 8000 should now be free. Starting backend..." -ForegroundColor Green
Write-Host "Run: python run.py" -ForegroundColor Cyan

