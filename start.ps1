Set-Location $PSScriptRoot
$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $listener) { Start-Process -FilePath python -ArgumentList "div.py" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden }
Start-Process "http://127.0.0.1:8000/"
