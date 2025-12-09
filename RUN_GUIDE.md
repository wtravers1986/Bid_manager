# How to Run the AI Lifting Document Cleanup Tool

## Prerequisites

### Required
- **Docker & Docker Compose** (for easiest setup)
  - Download: https://www.docker.com/products/docker-desktop
- **Azure Resources** (you need these to use the AI features):
  - Azure OpenAI Service (with GPT-4 deployment)
  - Azure AI Search Service
  - Azure Blob Storage Account


---

## Docker Setup

### Step 1: Create Environment File

Copy the template and create a `.env` file in the project root:

```bash
# Copy the template
cp env.template .env

# Or create manually with your Azure credentials
```

The `.env` file should contain:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Local Vector Store (HNSW) - No configuration needed
# Vectors are stored locally in data/vector_index.bin

# Local Filesystem Storage (optional - defaults to ./data)
DATA_DIRECTORY=./data

# Application Settings (optional - defaults shown)
DEBUG=true
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/lifting_cleanup
REDIS_URL=redis://redis:6379/0
```

### Step 2: Start Services

```bash
# Start all services (PostgreSQL, Redis, Backend)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

### Step 3: Verify It's Running

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Root Endpoint**: http://localhost:8000

### Step 4: Add Documents

**Option A: Place files in data folder and scan**
1. Place your PDF/DOCX files in the `data/` folder (root level)
2. Create a session: **POST /api/v1/sessions**
3. Scan and import: **POST /api/v1/documents/scan-data-folder/{session_id}**

**Option B: Upload via API**
1. Create a session: **POST /api/v1/sessions**
2. Upload documents: **POST /api/v1/documents/upload/{session_id}**

### Step 5: Index Documents to Local HNSW Vector Store

**Option A: Index from data folder (Recommended)**
1. Place PDF/DOCX files in the `data/` folder
2. View vector store schema: **GET /api/v1/documents/index-schema**
3. Index documents: **POST /api/v1/documents/index-data-folder?session_id=1**

This will:
- Parse all documents
- Generate embeddings using Azure OpenAI
- Index all chunks in local HNSW vector store (saved to `data/vector_index.bin`)
- Enable semantic search without Azure AI Search

**Option B: Scan and import to database first**
1. **POST /api/v1/sessions** - Create a new session
2. **POST /api/v1/documents/scan-data-folder/{session_id}** - Scan data folder for documents
3. Then index: **POST /api/v1/documents/index-data-folder?session_id={session_id}**

### Step 6: Search Documents

After indexing, you can search:

```bash
POST /api/v1/search/search
{
  "query": "What are the safety requirements?",
  "top_k": 10
}
```

### Step 7: Test the API

Open http://localhost:8000/docs and try:
1. **POST /api/v1/sessions** - Create a new session
2. **GET /api/v1/documents/index-schema** - View vector store schema
3. **POST /api/v1/documents/index-data-folder** - Index documents from data folder
4. **POST /api/v1/search/search** - Search indexed documents
5. **GET /api/v1/search/stats** - View vector store statistics

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
```

### Azure Connection Issues

1. **Verify credentials** in `.env` file
2. **Check network connectivity** to Azure
3. **Verify Azure resources** are provisioned:
   - Azure OpenAI Service with GPT-4 deployment
   - Azure AI Search Service (Standard tier or higher for vector search)
   - Azure Blob Storage Account

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing environment variables
# - Database not ready (wait a few seconds)
# - Port 8000 already in use
```


---

## Quick Test

Once running, test the API:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Create a session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Session",
    "description": "Testing the API"
  }'

# 3. Check API docs
# Open browser: http://localhost:8000/docs
```

---

## Development Workflow

### Database Migrations

Currently using SQLAlchemy's `create_all()`. For production, consider using Alembic migrations.

---

## Production Deployment

See `docs/DEPLOYMENT.md` for production deployment instructions.

---

## Next Steps

1. ✅ Verify API is running: http://localhost:8000/docs
2. 📖 Read [USER_GUIDE.md](docs/USER_GUIDE.md) for usage instructions
3. 🏗️ Check [ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details
4. 🚀 Start creating sessions and uploading documents!

---

**Note**: Some features require additional setup:
- SharePoint integration (not yet implemented)
- Celery workers for async tasks (not yet implemented)
- Word/PDF output generation (not yet implemented)

The core API and AI analysis features should work once Azure credentials are configured.

