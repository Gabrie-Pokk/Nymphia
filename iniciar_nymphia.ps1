# ==============================================================================
# NYMPHIA — SCRIPT DE INICIALIZAÇÃO LOCAL COM ACESSO MOBILE (WI-FI)
# ==============================================================================

$Host.UI.RawUI.WindowTitle = "Nymphia — Start-up de IA Obstétrica"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Identifica o IP local na rede Wi-Fi / Ethernet
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' -and $_.InterfaceAlias -notmatch 'VPN'
} | Select-Object -First 1).IPAddress

if (-not $ipAddress) {
    $ipAddress = "127.0.0.1"
}

Write-Host "=================================================================" -ForegroundColor DarkRed
Write-Host "      NYMPHIA — CADA BATIMENTO IMPORTA" -ForegroundColor DarkMagenta
Write-Host "      Iniciando Plataforma de IA & Frontend PWA Mobile" -ForegroundColor DarkYellow
Write-Host "=================================================================" -ForegroundColor DarkRed
Write-Host ""
Write-Host "-> Acesso no seu PC:       http://localhost:5173" -ForegroundColor Green
Write-Host "-> Acesso no seu Celular:  http://$($ipAddress):5173" -ForegroundColor Cyan
Write-Host "-> Backend & Modelos IA:   http://$($ipAddress):8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione qualquer tecla para encerrar os servidores quando desejar." -ForegroundColor Gray
Write-Host ""

# Inicia Backend em segundo plano
$backendProcess = Start-Process -FilePath "$scriptDir\nymphia_backend\.venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" `
    -WorkingDirectory "$scriptDir\nymphia_backend" `
    -PassThru -NoNewWindow

# Inicia Frontend Vite em segundo plano
$frontendProcess = Start-Process -FilePath "npm" `
    -ArgumentList "run dev -- --host 0.0.0.0" `
    -WorkingDirectory "$scriptDir\frontend" `
    -PassThru -NoNewWindow

try {
    [Console]::ReadKey($true) | Out-Null
} finally {
    Write-Host "`nEncerrando servidores Nymphia..." -ForegroundColor Yellow
    if ($backendProcess -and -not $backendProcess.HasExited) { Stop-Process -Id $backendProcess.Id -Force }
    if ($frontendProcess -and -not $frontendProcess.HasExited) { Stop-Process -Id $frontendProcess.Id -Force }
    Write-Host "Servidores encerrados com sucesso." -ForegroundColor Green
}
