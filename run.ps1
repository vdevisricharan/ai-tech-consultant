# One-command runner for Windows PowerShell
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "           Launching AI Tech Consultant Microservices           " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python run_all.py
