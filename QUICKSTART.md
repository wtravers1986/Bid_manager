# Quick Start Guide

## Get Started in 5 Minutes

### Prerequisites

- **Docker Desktop** installed and running
- **Azure OpenAI** credentials (endpoint, API key, deployment names)
- **Git** (optional, for cloning)

### Step 1: Clone or Download Repository

```bash
git clone <repository-url>
cd "deme demo"
```

Of download en extract de repository.

### Step 2: Configure Environment

1. **Copy the environment template:**
   ```bash
   cp env.template .env
   ```

2. **Edit `.env` file with your Azure OpenAI credentials:**
   ```bash
   # Windows (Notepad)
   notepad .env
   
   # Linux/Mac
   nano .env
   ```

3. **Required Azure OpenAI settings:**
   ```ini
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt-4-deployment
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your-embedding-deployment
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

   **Important:** 
   - Endpoint should NOT include `/openai/v1/` (it's added automatically)
   - Use your actual deployment names from Azure Portal

### Step 3: Prepare Documents (Optional)

Place PDF or DOCX files in the `data/` folder:
```bash
# Create data folder if it doesn't exist
mkdir -p data

# Copy your documents
cp /path/to/your/documents/*.pdf data/
```

### Step 4: Start Docker Services

```bash
# Start all services in detached mode
docker-compose up -d

# Check service status
docker-compose ps

# View logs (optional)
docker-compose logs -f backend
```

**Expected output:**
```
[+] Running 4/4
 ✔ Container lifting-cleanup-db         Healthy
 ✔ Container lifting-cleanup-redis    Healthy
 ✔ Container lifting-cleanup-backend  Started
 ✔ Container lifting-cleanup-streamlit Started
```

### Step 5: Access the Application

Once services are running, access:

- **🎨 Streamlit Frontend (Main Interface)**: http://localhost:8501
- **🔧 Backend API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **❤️ Health Check**: http://localhost:8000/health

### Step 6: Index Documents

1. Open **http://localhost:8501** in your browser
2. Go to the **"📄 Index Documents"** tab
3. Click **"Index All Documents"**
4. Wait for indexing to complete (you'll see a success message)

**Note:** This step uses LLM-based chunking for better paragraph boundaries.

### Step 7: Create Your First Synthesis

1. Go to the **"📝 Synthesis"** tab in Streamlit
2. **Step 1:** Enter a session name and select PDF files
3. Click **"➕ Create Session"**
4. **Step 2:** Click **"🔍 Analyze Structures & Generate Inventory Table"**
5. **Step 3:** Review and edit the inventory table, then save
6. **Step 4:** For each section, click **"🔍 Find Paragraphs"** and select relevant paragraphs
7. **Step 5:** Click **"📝 Generate Final Document"** and download the DOCX

See [DEMO_SYNTHESIS.md](DEMO_SYNTHESIS.md) for detailed step-by-step instructions.

## Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend      # Backend logs
docker-compose logs -f streamlit    # Streamlit logs
docker-compose logs -f              # All logs

# Restart a specific service
docker-compose restart backend
docker-compose restart streamlit

# Rebuild after code changes
docker-compose build backend
docker-compose build streamlit
docker-compose up -d

# Check service health
docker-compose ps
curl http://localhost:8000/health
```

## Troubleshooting

### Services won't start?
```bash
# Check logs for errors
docker-compose logs

# Restart all services
docker-compose restart

# Full restart (clears volumes)
docker-compose down
docker-compose up -d
```

### Can't connect to Azure OpenAI?
- ✅ Verify credentials in `.env` file
- ✅ Check endpoint URL (should NOT include `/openai/v1/`)
- ✅ Verify deployment names match Azure Portal
- ✅ Check API key is valid and not expired
- ✅ Ensure network connectivity to Azure

### Backend container keeps restarting?
```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# - Missing .env file
# - Invalid Azure credentials
# - Database connection issues
```

### Streamlit shows "No PDFs found"?
- ✅ Ensure PDF files are in `./data/` folder
- ✅ Check file permissions
- ✅ Restart streamlit: `docker-compose restart streamlit`

### Database errors?
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Port already in use?
```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Linux/Mac:
lsof -i :8000
lsof -i :8501

# Change ports in docker-compose.yml if needed
```

## Next Steps

- 📖 Read [DEMO_SYNTHESIS.md](DEMO_SYNTHESIS.md) for detailed synthesis workflow
- 🔍 Explore the [API Documentation](http://localhost:8000/docs)
- 📚 Check the main [README.md](README.md) for architecture details

## Access Points Summary

| Service | URL | Description |
|---------|-----|-------------|
| **Streamlit UI** | http://localhost:8501 | Main user interface |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | Service health status |

---

Happy consolidating! 🚀
