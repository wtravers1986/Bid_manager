# Ngrok Setup voor Public Access

Deze gids helpt je om de applicatie publiek toegankelijk te maken via ngrok.

## 📋 Vereisten

1. **Ngrok account** (gratis): https://ngrok.com/signup
2. **Ngrok geïnstalleerd** op je machine
3. **Docker services draaiend** (zie `START_HIER.md`)

## 🚀 Snelle Start

### Stap 1: Installeer Ngrok

**Optie A: Via winget (aanbevolen voor Windows)**
```powershell
winget install ngrok.ngrok
```

**Optie B: Via Chocolatey**
```powershell
choco install ngrok
```

**Optie C: Via Scoop**
```powershell
scoop install ngrok
```

**Optie D: Handmatig downloaden**
1. Ga naar https://ngrok.com/download
2. Download de Windows versie
3. Pak uit en voeg toe aan PATH

### Stap 2: Configureer Ngrok Authtoken

1. Ga naar https://dashboard.ngrok.com/get-started/your-authtoken
2. Log in met je ngrok account
3. Kopieer je authtoken
4. Voer uit in PowerShell:

```powershell
ngrok config add-authtoken <jouw-authtoken>
```

### Stap 3: Start Docker Services

Zorg dat alle services draaien:

```powershell
docker compose up -d
```

Verifieer dat alles draait:

```powershell
docker compose ps
```

### Stap 4: Start Ngrok Tunnels

**Gebruik het setup script (aanbevolen):**

```powershell
.\setup-ngrok.ps1
```

**Of handmatig:**

```powershell
# Start backend tunnel
Start-Process ngrok -ArgumentList "http", "8000"

# Start streamlit tunnel (in nieuwe terminal)
Start-Process ngrok -ArgumentList "http", "8501"
```

**Of gebruik ngrok config file voor beide tunnels:**

```powershell
ngrok start --all
```

### Stap 5: Update CORS Settings

1. Open de ngrok web interface: http://localhost:4040
2. Kopieer de publieke URLs (bijv. `https://abc123.ngrok-free.app`)
3. Open `.env` bestand
4. Update `CORS_ORIGINS` met de ngrok URLs:

```env
# Voeg ngrok URLs toe aan CORS_ORIGINS (gescheiden door komma's)
CORS_ORIGINS=http://localhost:3000,https://abc123.ngrok-free.app,https://def456.ngrok-free.app
```

5. Herstart de backend service:

```powershell
docker compose restart backend
```

## 🌐 Ngrok URLs Ophalen

### Via Web Interface

1. Open http://localhost:4040
2. Je ziet beide tunnels met hun publieke URLs
3. Kopieer de HTTPS URLs

### Via Command Line

```powershell
# Backend URL
curl http://localhost:4040/api/tunnels | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Where-Object { $_.config.addr -eq "localhost:8000" } | Select-Object -ExpandProperty public_url

# Streamlit URL
curl http://localhost:4040/api/tunnels | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Where-Object { $_.config.addr -eq "localhost:8501" } | Select-Object -ExpandProperty public_url
```

## 📝 Ngrok Configuratie Bestand

Het script maakt automatisch een configuratie bestand aan op:
`%USERPROFILE%\.ngrok2\ngrok.yml`

Je kunt dit handmatig aanpassen voor geavanceerde configuratie:

```yaml
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
```

## 🔒 Security Overwegingen

⚠️ **Belangrijk voor productie:**

1. **Ngrok gratis plan**: URLs veranderen bij elke restart
2. **Geen authenticatie**: Iedereen met de URL kan toegang krijgen
3. **Rate limits**: Gratis plan heeft beperkingen
4. **Voor productie**: Gebruik Azure Container Apps of andere cloud services

### Aanbevolen voor Public Access:

1. **Ngrok betaald plan** voor statische URLs
2. **Basic Auth toevoegen** via ngrok:
   ```powershell
   ngrok http 8000 --basic-auth="username:password"
   ```
3. **IP whitelisting** (betaald plan)
4. **Custom domain** (betaald plan)

## 🛠️ Troubleshooting

### Ngrok start niet

```powershell
# Check of ngrok geïnstalleerd is
ngrok version

# Check authenticatie
ngrok config check

# Test met eenvoudige tunnel
ngrok http 8000
```

### CORS errors

1. Controleer of ngrok URLs in `CORS_ORIGINS` staan
2. Herstart backend: `docker compose restart backend`
3. Check backend logs: `docker compose logs backend`

### Services niet bereikbaar

1. Check of Docker services draaien: `docker compose ps`
2. Test lokale toegang: `curl http://localhost:8000/health`
3. Check ngrok status: http://localhost:4040

### Port al in gebruik

Als ngrok meldt dat een poort al in gebruik is:

```powershell
# Check welke processen poorten gebruiken
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Stop andere ngrok instances
Get-Process ngrok | Stop-Process
```

## 📊 Monitoring

### Ngrok Dashboard

Open http://localhost:4040 voor:
- Live request monitoring
- Request/response inspectie
- Tunnel status
- Publieke URLs

### Ngrok API

```powershell
# Get tunnel info
curl http://localhost:4040/api/tunnels

# Get requests
curl http://localhost:4040/api/requests/http
```

## 🎯 Gebruik

Na setup:

1. **Streamlit Frontend**: Gebruik de streamlit ngrok URL
2. **Backend API**: Gebruik de backend ngrok URL
3. **API Docs**: `https://<backend-ngrok-url>/docs`

Deel de URLs met anderen om toegang te geven (let op security!).

## 🔄 Herstarten

Als je ngrok moet herstarten:

```powershell
# Stop alle ngrok processen
Get-Process ngrok | Stop-Process

# Start opnieuw
.\setup-ngrok.ps1
```

**Let op**: De URLs veranderen bij herstart (gratis plan). Update `CORS_ORIGINS` en herstart backend.

## 📚 Meer Informatie

- Ngrok documentatie: https://ngrok.com/docs
- Ngrok dashboard: https://dashboard.ngrok.com
- Ngrok pricing: https://ngrok.com/pricing










