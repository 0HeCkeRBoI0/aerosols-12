Set-Location $PSScriptRoot
Start-Process -FilePath python -ArgumentList "div.py" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
Write-Host "SAMADHAN is available at http://127.0.0.1:8000 (and port 8000 on this computer's local network)."
