# Start Instructies

## Vereisten
- Docker en Docker Compose geïnstalleerd
- Een `.env` bestand met Azure OpenAI credentials

## Stap 1: Maak een .env bestand

Kopieer `env.template` naar `.env` en vul de Azure OpenAI credentials in:

```bash
# Op Windows PowerShell:
Copy-Item env.template .env

# Op Linux/Mac:
cp env.template .env
```

Bewerk `.env` en vul de volgende waarden in:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`

## Stap 2: Start de applicatie

```bash
docker compose up -d
```

Dit start:
- PostgreSQL database (poort 5432)
- Redis cache (poort 6379)
- Backend API (poort 8000)
- Streamlit frontend (poort 8501)

## Stap 3: Open de applicatie

- Streamlit UI: http://localhost:8501
- Backend API docs: http://localhost:8000/docs

## Stoppen

```bash
docker compose down
```

## Problemen oplossen

Als er problemen zijn:
1. Controleer of Docker draait
2. Controleer of de poorten 5432, 6379, 8000, 8501 vrij zijn
3. Bekijk de logs: `docker compose logs`
4. Herstart: `docker compose restart`

