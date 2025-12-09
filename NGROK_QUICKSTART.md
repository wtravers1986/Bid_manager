# 🚀 Ngrok Quick Start

Je applicatie is klaar om publiek toegankelijk te maken via ngrok!

## ✅ Wat is al gedaan

1. ✅ Ngrok is geïnstalleerd
2. ✅ CORS instellingen zijn bijgewerkt (alle origins toegestaan in development)
3. ✅ Backend is herstart met nieuwe CORS instellingen
4. ✅ Scripts zijn aangemaakt om ngrok te starten

## 📝 Wat je nog moet doen

### Stap 1: Ngrok Account & Authtoken

1. **Maak een gratis ngrok account** (als je die nog niet hebt):
   - Ga naar: https://ngrok.com/signup
   - Maak een account aan

2. **Haal je authtoken op**:
   - Ga naar: https://dashboard.ngrok.com/get-started/your-authtoken
   - Log in met je account
   - Kopieer je authtoken

3. **Configureer ngrok**:
   ```powershell
   ngrok config add-authtoken <jouw-authtoken>
   ```
   Vervang `<jouw-authtoken>` met het token dat je hebt gekopieerd.

### Stap 2: Start Ngrok Tunnels

Zodra ngrok is geconfigureerd, start de tunnels:

```powershell
.\start-ngrok.ps1
```

Dit script:
- ✅ Controleert of Docker services draaien
- ✅ Start ngrok tunnels voor Backend (poort 8000) en Streamlit (poort 8501)
- ✅ Toont de publieke URLs

### Stap 3: Bekijk Publieke URLs

1. **Via Web Interface** (aanbevolen):
   - Open: http://localhost:4040
   - Je ziet beide tunnels met hun publieke HTTPS URLs
   - Kopieer de URLs

2. **Via Command Line**:
   ```powershell
   curl http://localhost:4040/api/tunnels | ConvertFrom-Json
   ```

## 🌐 Gebruik

Na het starten krijg je twee publieke URLs:

- **Backend API**: `https://xxxx-xxxx.ngrok-free.app`
  - API Docs: `https://xxxx-xxxx.ngrok-free.app/docs`
  - Health: `https://xxxx-xxxx.ngrok-free.app/health`

- **Streamlit Frontend**: `https://yyyy-yyyy.ngrok-free.app`
  - Direct toegang tot de applicatie

## 📋 Handige Commands

```powershell
# Start ngrok tunnels
.\start-ngrok.ps1

# Stop ngrok
Get-Process ngrok | Stop-Process

# Bekijk ngrok status
curl http://localhost:4040/api/tunnels

# Herstart ngrok (na configuratie wijzigingen)
Get-Process ngrok | Stop-Process
.\start-ngrok.ps1
```

## ⚠️ Belangrijke Notities

1. **Gratis Plan**: URLs veranderen bij elke restart
2. **Geen Authenticatie**: Iedereen met de URL kan toegang krijgen
3. **Rate Limits**: Gratis plan heeft beperkingen
4. **Voor Productie**: Gebruik Azure Container Apps of betaald ngrok plan

## 🔒 Security Tips

Voor publieke toegang:

1. **Basic Auth toevoegen** (aanbevolen):
   ```powershell
   # Stop huidige tunnels
   Get-Process ngrok | Stop-Process
   
   # Start met basic auth
   Start-Process ngrok -ArgumentList "http", "8000", "--basic-auth=username:password"
   Start-Process ngrok -ArgumentList "http", "8501", "--basic-auth=username:password"
   ```

2. **IP Whitelisting** (betaald plan)
3. **Custom Domain** (betaald plan)

## 🛠️ Troubleshooting

### "Ngrok is nog niet geconfigureerd"
- Volg Stap 1 hierboven om authtoken toe te voegen

### "Backend/Streamlit draait niet"
- Start Docker services: `docker compose up -d`
- Wacht tot services healthy zijn: `docker compose ps`

### CORS Errors
- CORS is al geconfigureerd om alle origins toe te staan in development
- Als je errors ziet, herstart backend: `docker compose restart backend`

### Port al in gebruik
```powershell
# Stop alle ngrok processen
Get-Process ngrok | Stop-Process

# Check welke processen poorten gebruiken
netstat -ano | findstr :8000
netstat -ano | findstr :8501
```

## 📚 Meer Informatie

- Volledige setup gids: `NGROK_SETUP.md`
- Ngrok documentatie: https://ngrok.com/docs
- Ngrok dashboard: https://dashboard.ngrok.com

---

**Klaar om te starten?** Voer `.\start-ngrok.ps1` uit na het configureren van je authtoken!










