# Ngrok Setup Script voor AI Lifting Document Cleanup Tool
# Dit script start ngrok tunnels voor Streamlit en Backend API

Write-Host "🌐 Ngrok Setup voor Public Access" -ForegroundColor Cyan
Write-Host ""

# Check if ngrok is installed
Write-Host "📦 Controleren of ngrok is geïnstalleerd..." -ForegroundColor Yellow
try {
    $ngrokVersion = ngrok version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Ngrok gevonden" -ForegroundColor Green
        Write-Host "   $ngrokVersion" -ForegroundColor Gray
    } else {
        throw "ngrok not found"
    }
} catch {
    Write-Host "❌ Ngrok is niet geïnstalleerd!" -ForegroundColor Red
    Write-Host ""
    Write-Host "📥 Installatie instructies:" -ForegroundColor Yellow
    Write-Host "   1. Download ngrok van: https://ngrok.com/download" -ForegroundColor White
    Write-Host "   2. Of installeer via Chocolatey: choco install ngrok" -ForegroundColor White
    Write-Host "   3. Of installeer via Scoop: scoop install ngrok" -ForegroundColor White
    Write-Host "   4. Of installeer via winget: winget install ngrok.ngrok" -ForegroundColor White
    Write-Host ""
    Write-Host "   Na installatie, registreer je account en haal je een authtoken op:" -ForegroundColor Yellow
    Write-Host "   - Ga naar https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
    Write-Host "   - Kopieer je authtoken" -ForegroundColor White
    Write-Host "   - Voer uit: ngrok config add-authtoken <jouw-token>" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Check if ngrok is authenticated
Write-Host "`n🔐 Controleren ngrok authenticatie..." -ForegroundColor Yellow
try {
    $ngrokConfig = ngrok config check 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Ngrok is geconfigureerd" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Ngrok authenticatie niet gevonden" -ForegroundColor Yellow
        Write-Host "   Voer uit: ngrok config add-authtoken <jouw-token>" -ForegroundColor White
        Write-Host "   Haal je token op van: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
    }
} catch {
    Write-Host "⚠️  Kon ngrok configuratie niet controleren" -ForegroundColor Yellow
}

# Check if services are running
Write-Host "`n🔍 Controleren of Docker services draaien..." -ForegroundColor Yellow
try {
    docker ps --filter "name=lifting-cleanup" --format "{{.Names}}" | Out-Null
    $services = docker ps --filter "name=lifting-cleanup" --format "{{.Names}}"
    if ($services) {
        Write-Host "✅ Docker services draaien:" -ForegroundColor Green
        $services | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
    } else {
        Write-Host "⚠️  Geen Docker services gevonden. Start eerst: docker compose up -d" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Kon Docker services niet controleren" -ForegroundColor Yellow
}

# Check if ports are in use
Write-Host "`n🔌 Controleren poorten..." -ForegroundColor Yellow
$backendPort = 8000
$streamlitPort = 8501

try {
    $backendTest = Test-NetConnection -ComputerName localhost -Port $backendPort -WarningAction SilentlyContinue
    if ($backendTest.TcpTestSucceeded) {
        Write-Host "✅ Backend API draait op poort $backendPort" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend API draait niet op poort $backendPort" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️  Kon poort $backendPort niet controleren" -ForegroundColor Yellow
}

try {
    $streamlitTest = Test-NetConnection -ComputerName localhost -Port $streamlitPort -WarningAction SilentlyContinue
    if ($streamlitTest.TcpTestSucceeded) {
        Write-Host "✅ Streamlit draait op poort $streamlitPort" -ForegroundColor Green
    } else {
        Write-Host "❌ Streamlit draait niet op poort $streamlitPort" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️  Kon poort $streamlitPort niet controleren" -ForegroundColor Yellow
}

# Create ngrok config file for multiple tunnels
Write-Host "`n📝 Aanmaken ngrok configuratie..." -ForegroundColor Yellow
$ngrokConfigPath = "$env:USERPROFILE\.ngrok2\ngrok.yml"
$ngrokConfigDir = Split-Path -Path $ngrokConfigPath -Parent

if (-not (Test-Path $ngrokConfigDir)) {
    New-Item -ItemType Directory -Path $ngrokConfigDir -Force | Out-Null
}

# Create or update ngrok config
$ngrokConfigContent = @"
version: "2"
authtoken_from_env: true
tunnels:
  backend:
    addr: 8000
    proto: http
    bind_tls: true
  streamlit:
    addr: 8501
    proto: http
    bind_tls: true
"@

# Check if config exists and ask to update
if (Test-Path $ngrokConfigPath) {
    Write-Host "⚠️  Ngrok configuratie bestaat al op: $ngrokConfigPath" -ForegroundColor Yellow
    Write-Host "   Wil je deze overschrijven? (j/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "j" -or $response -eq "J" -or $response -eq "y" -or $response -eq "Y") {
        $ngrokConfigContent | Out-File -FilePath $ngrokConfigPath -Encoding utf8
        Write-Host "✅ Ngrok configuratie bijgewerkt" -ForegroundColor Green
    } else {
        Write-Host "⏭️  Configuratie niet gewijzigd" -ForegroundColor Gray
    }
} else {
    $ngrokConfigContent | Out-File -FilePath $ngrokConfigPath -Encoding utf8
    Write-Host "✅ Ngrok configuratie aangemaakt op: $ngrokConfigPath" -ForegroundColor Green
}

# Start ngrok
Write-Host "`n🚀 Starten ngrok tunnels..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Dit start twee tunnels:" -ForegroundColor Yellow
Write-Host "   - Backend API (poort 8000)" -ForegroundColor White
Write-Host "   - Streamlit Frontend (poort 8501)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Let op: Deze terminal blijft open zolang ngrok draait." -ForegroundColor Yellow
Write-Host "   Druk Ctrl+C om te stoppen." -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 Ngrok web interface: http://localhost:4040" -ForegroundColor Cyan
Write-Host ""

# Start ngrok with config file
Start-Process -FilePath "ngrok" -ArgumentList "start", "--all", "--config", $ngrokConfigPath -NoNewWindow

Write-Host "✅ Ngrok tunnels gestart!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Volgende stappen:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:4040 in je browser om de ngrok dashboard te zien" -ForegroundColor White
Write-Host "   2. Kopieer de publieke URLs voor backend en streamlit" -ForegroundColor White
Write-Host "   3. Update CORS_ORIGINS in .env met de ngrok URLs (zie instructies hieronder)" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: De ngrok URLs veranderen elke keer dat je ngrok herstart (gratis plan)" -ForegroundColor Yellow
Write-Host "   Overweeg een betaald plan voor statische URLs" -ForegroundColor Yellow










