# Streamlit Interface

Een gebruiksvriendelijke web interface voor de AI Document Cleanup Tool.

## Features

- 🔍 **Semantic Search**: Zoek door geïndexeerde documenten met semantische zoekopdrachten
- 📄 **Document Indexering**: Indexeer documenten uit de data folder
- 📊 **Statistieken**: Bekijk vector store statistieken
- ⚙️ **Management**: Beheer de vector index

## Gebruik

### Via Docker Compose

De Streamlit interface is automatisch beschikbaar op **http://localhost:8501** wanneer je `docker-compose up` uitvoert.

### Lokaal (Development)

```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

## Interface Tabs

### 1. Search Tab
- Voer semantische zoekopdrachten uit
- Pas het aantal resultaten aan (top_k)
- Bekijk gedetailleerde resultaten met metadata

### 2. Index Documents Tab
- Indexeer alle documenten uit de data folder
- Bekijk verwerkingsstatistieken
- Bekijk vector store schema

### 3. Statistics Tab
- Bekijk vector store statistieken
- Totaal aantal vectors, dimensies, etc.

### 4. Management Tab
- Wis de vector index (voorzichtig!)
- Bekijk API informatie
- Open API documentatie

## Configuratie

De API URL wordt automatisch geconfigureerd via de `API_BASE_URL` environment variable in docker-compose.yml.

Voor lokale ontwikkeling kan je de API URL aanpassen in de sidebar.

