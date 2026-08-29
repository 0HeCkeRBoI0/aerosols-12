Set-Location $PSScriptRoot

$port = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$server = $null
if (-not $port) {
    $server = Start-Process -FilePath python -ArgumentList "div.py" -WorkingDirectory $PSScriptRoot -PassThru
}
$ready = $false
for ($attempt = 0; $attempt -lt 100; $attempt++) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("127.0.0.1", 8000)
        $client.Close()
        $ready = $true
        break
    } catch {
        if ($server -and $server.HasExited) { break }
    }
}
if ($ready) {
    $localAddress = (Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike "169.254.*" -and $_.IPAddress -ne "127.0.0.1" } |
        Select-Object -First 1 -ExpandProperty IPAddress)
    Write-Host "Laptop URL: http://127.0.0.1:8000/"
    if ($localAddress) { Write-Host "Phone/tablet URL (same Wi-Fi): http://$localAddress`:8000/" }
    Start-Process "http://127.0.0.1:8000/"
} else {
    Write-Error "Common Ground could not start on port 8000. Check whether another server is using that port."
    if ($server -and -not $server.HasExited) { Stop-Process $server.Id -Force }
    exit 1
}
