# Quick Start Script voor Ngrok Tunnels
# Start ngrok tunnels voor Backend en Streamlit

Write-Host "🌐 Ngrok Tunnels Starten" -ForegroundColor Cyan
Write-Host ""

# Check ngrok installation
try {
    $null = ngrok version 2>&1
    Write-Host "✅ Ngrok gevonden" -ForegroundColor Green
} catch {
    Write-Host "❌ Ngrok niet gevonden. Installeer eerst: winget install ngrok.ngrok" -ForegroundColor Red
    exit 1
}

# Check if authtoken is configured
$ngrokConfigPath = "$env:LOCALAPPDATA\ngrok\ngrok.yml"
if (-not (Test-Path $ngrokConfigPath)) {
    Write-Host "⚠️  Ngrok is nog niet geconfigureerd!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📝 Stap 1: Maak een gratis ngrok account op https://ngrok.com/signup" -ForegroundColor White
    Write-Host "📝 Stap 2: Haal je authtoken op: https://dashboard.ngrok.com/get-started/your-authtoken" -ForegroundColor White
    Write-Host "📝 Stap 3: Voer uit: ngrok config add-authtoken <jouw-token>" -ForegroundColor White
    Write-Host ""
    Write-Host "Daarna kun je dit script opnieuw uitvoeren." -ForegroundColor Yellow
    exit 1
}

# Check if services are running
Write-Host "🔍 Controleren Docker services..." -ForegroundColor Yellow
$backendRunning = $false
$streamlitRunning = $false

try {
    $backendTest = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue -InformationLevel Quiet
    $streamlitTest = Test-NetConnection -ComputerName localhost -Port 8501 -WarningAction SilentlyContinue -InformationLevel Quiet
    
    if ($backendTest) {
        Write-Host "✅ Backend draait op poort 8000" -ForegroundColor Green
        $backendRunning = $true
    } else {
        Write-Host "❌ Backend draait niet op poort 8000" -ForegroundColor Red
        Write-Host "   Start eerst: docker compose up -d" -ForegroundColor Yellow
    }
    
    if ($streamlitTest) {
        Write-Host "✅ Streamlit draait op poort 8501" -ForegroundColor Green
        $streamlitRunning = $true
    } else {
        Write-Host "❌ Streamlit draait niet op poort 8501" -ForegroundColor Red
        Write-Host "   Start eerst: docker compose up -d" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Kon services niet controleren" -ForegroundColor Yellow
}

if (-not ($backendRunning -and $streamlitRunning)) {
    Write-Host ""
    Write-Host "⚠️  Start eerst de Docker services voordat je ngrok start!" -ForegroundColor Red
    exit 1
}

# Check if ngrok is already running
$ngrokProcesses = Get-Process -Name ngrok -ErrorAction SilentlyContinue
if ($ngrokProcesses) {
    Write-Host "⚠️  Ngrok draait al!" -ForegroundColor Yellow
    Write-Host "   Stop eerst bestaande ngrok processen:" -ForegroundColor Yellow
    Write-Host "   Get-Process ngrok | Stop-Process" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "Wil je bestaande processen stoppen en opnieuw starten? (j/n)"
    if ($response -eq "j" -or $response -eq "J" -or $response -eq "y" -or $response -eq "Y") {
        Get-Process -Name ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
        Start-Sleep -Seconds 2
        Write-Host "✅ Bestaande ngrok processen gestopt" -ForegroundColor Green
    } else {
        Write-Host "⏭️  Ngrok niet herstart" -ForegroundColor Gray
        exit 0
    }
}

Write-Host ""
Write-Host "🚀 Starten ngrok tunnels..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Dit start twee tunnels:" -ForegroundColor Yellow
Write-Host "   📡 Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "   🎨 Streamlit UI:   http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Ngrok Dashboard: http://localhost:4040" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Deze terminal blijft open zolang ngrok draait." -ForegroundColor Yellow
Write-Host "   Druk Ctrl+C om te stoppen." -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Na het starten:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:4040 om de publieke URLs te zien" -ForegroundColor White
Write-Host "   2. Kopieer de HTTPS URLs voor backend en streamlit" -ForegroundColor White
Write-Host "   3. Deel deze URLs om publieke toegang te geven" -ForegroundColor White
Write-Host ""

# Start ngrok with both tunnels
# Using ngrok start --all requires a config file, so we'll start them separately
Write-Host "⏳ Starten tunnels..." -ForegroundColor Yellow

# Start ngrok for backend in background
Start-Process -FilePath "ngrok" -ArgumentList "http", "8000", "--log=stdout" -WindowStyle Hidden

# Wait a moment
Start-Sleep -Seconds 2

# Start ngrok for streamlit in background  
Start-Process -FilePath "ngrok" -ArgumentList "http", "8501", "--log=stdout" -WindowStyle Hidden

# Wait a moment for tunnels to establish
Start-Sleep -Seconds 3

Write-Host "✅ Ngrok tunnels gestart!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Om de URLs te zien:" -ForegroundColor Cyan
Write-Host "   - Open http://localhost:4040 in je browser" -ForegroundColor White
Write-Host "   - Of gebruik de API: curl http://localhost:4040/api/tunnels" -ForegroundColor White
Write-Host ""

# Try to get URLs from ngrok API
try {
    Start-Sleep -Seconds 2
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction SilentlyContinue
    if ($tunnels.tunnels) {
        Write-Host "🌐 Publieke URLs:" -ForegroundColor Green
        foreach ($tunnel in $tunnels.tunnels) {
            $name = if ($tunnel.config.addr -eq "localhost:8000") { "Backend API" } 
                   elseif ($tunnel.config.addr -eq "localhost:8501") { "Streamlit UI" }
                   else { "Tunnel" }
            Write-Host "   $name : $($tunnel.public_url)" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "   (URLs worden geladen, probeer over een paar seconden opnieuw)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "💡 Tip: De URLs veranderen bij elke restart (gratis plan)" -ForegroundColor Yellow
Write-Host "   Overweeg een betaald plan voor statische URLs" -ForegroundColor Yellow
Write-Host ""
Write-Host "🛑 Om te stoppen: Get-Process ngrok | Stop-Process" -ForegroundColor Gray










