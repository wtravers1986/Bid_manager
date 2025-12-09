# Deployment Guide

## Prerequisites

### Required Azure Resources

Before deploying, you need to provision the following Azure resources:

1. **Azure OpenAI Service**
   - GPT-4 deployment for text generation
   - text-embedding-ada-002 deployment for embeddings
   - Note the endpoint and API key

2. **Azure AI Search**
   - Standard or higher tier for vector search
   - Note the endpoint and API key

3. **Azure Blob Storage**
   - Storage account with three containers:
     - `source-documents`: For uploaded documents
     - `output-documents`: For generated outputs
     - `archive-documents`: For archived old documents
   - Note the connection string

4. **Azure PostgreSQL** (optional for cloud deployment)
   - Flexible Server recommended
   - Database: `lifting_cleanup`

5. **Azure Container Apps** (for production deployment)
   - Or Azure App Service as alternative

### Local Development Requirements

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Git

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd demepoc
```

### 2. Configure Environment

Create `.env` file in the project root:

```bash
# Copy example env file
cp backend/.env.example .env

# Edit with your Azure credentials
nano .env
```

Required environment variables:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=lifting-docs

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

### 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

Services will be available at:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432
- Redis: localhost:6379

### 4. Initialize Database

The database will be automatically initialized on first run. To manually run migrations:

```bash
# Access backend container
docker-compose exec backend bash

# Run migrations (if using Alembic)
# alembic upgrade head
```

### 5. Create Azure AI Search Index

```bash
# Use the API endpoint to create the index
curl -X POST http://localhost:8000/api/v1/admin/create-index
```

## Production Deployment to Azure

### Option 1: Azure Container Apps (Recommended)

#### 1. Build and Push Docker Images

```bash
# Login to Azure Container Registry
az acr login --name yourregistry

# Build and tag backend
docker build -t yourregistry.azurecr.io/lifting-cleanup-backend:latest ./backend
docker push yourregistry.azurecr.io/lifting-cleanup-backend:latest

# Build and tag frontend
docker build -t yourregistry.azurecr.io/lifting-cleanup-frontend:latest ./frontend
docker push yourregistry.azurecr.io/lifting-cleanup-frontend:latest
```

#### 2. Deploy with Azure CLI

```bash
# Create resource group
az group create --name lifting-cleanup-rg --location westeurope

# Create Container Apps environment
az containerapp env create \
  --name lifting-cleanup-env \
  --resource-group lifting-cleanup-rg \
  --location westeurope

# Deploy backend
az containerapp create \
  --name lifting-cleanup-backend \
  --resource-group lifting-cleanup-rg \
  --environment lifting-cleanup-env \
  --image yourregistry.azurecr.io/lifting-cleanup-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server yourregistry.azurecr.io \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=secretref:openai-endpoint \
    AZURE_OPENAI_API_KEY=secretref:openai-key \
    DATABASE_URL=secretref:database-url

# Deploy frontend
az containerapp create \
  --name lifting-cleanup-frontend \
  --resource-group lifting-cleanup-rg \
  --environment lifting-cleanup-env \
  --image yourregistry.azurecr.io/lifting-cleanup-frontend:latest \
  --target-port 80 \
  --ingress external
```

#### 3. Configure Secrets

```bash
# Add secrets to Container Apps
az containerapp secret set \
  --name lifting-cleanup-backend \
  --resource-group lifting-cleanup-rg \
  --secrets \
    openai-endpoint=https://your-resource.openai.azure.com/ \
    openai-key=your-api-key \
    database-url=postgresql+asyncpg://...
```

### Option 2: Azure App Service

#### 1. Create App Service Plan

```bash
az appservice plan create \
  --name lifting-cleanup-plan \
  --resource-group lifting-cleanup-rg \
  --sku P1V2 \
  --is-linux
```

#### 2. Create Web Apps

```bash
# Backend
az webapp create \
  --resource-group lifting-cleanup-rg \
  --plan lifting-cleanup-plan \
  --name lifting-cleanup-backend \
  --deployment-container-image-name yourregistry.azurecr.io/lifting-cleanup-backend:latest

# Configure settings
az webapp config appsettings set \
  --resource-group lifting-cleanup-rg \
  --name lifting-cleanup-backend \
  --settings \
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
    AZURE_OPENAI_API_KEY=@Microsoft.KeyVault(SecretUri=...)
```

### Option 3: Azure Kubernetes Service (AKS)

For larger deployments with high scalability requirements, see `docs/kubernetes-deployment.md`.

## Post-Deployment Configuration

### 1. Database Migrations

```bash
# Run on deployed backend
az containerapp exec \
  --name lifting-cleanup-backend \
  --resource-group lifting-cleanup-rg \
  --command "alembic upgrade head"
```

### 2. Create Search Index

```bash
# Call admin endpoint
curl -X POST https://your-backend.azurecontainerapps.io/api/v1/admin/create-index \
  -H "Authorization: Bearer <admin-token>"
```

### 3. Setup Monitoring

```bash
# Enable Application Insights
az monitor app-insights component create \
  --app lifting-cleanup-insights \
  --location westeurope \
  --resource-group lifting-cleanup-rg \
  --application-type web

# Get instrumentation key and add to backend env vars
```

### 4. Configure Auto-scaling

```bash
# Configure scale rules for Container Apps
az containerapp update \
  --name lifting-cleanup-backend \
  --resource-group lifting-cleanup-rg \
  --min-replicas 1 \
  --max-replicas 10 \
  --scale-rule-name http-requests \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50
```

## Monitoring & Maintenance

### Health Checks

- Backend health: `GET /health`
- Database connectivity: Monitored automatically
- Azure services: Check Azure Portal

### Logs

```bash
# View backend logs
az containerapp logs show \
  --name lifting-cleanup-backend \
  --resource-group lifting-cleanup-rg \
  --follow

# Or using Docker Compose locally
docker-compose logs -f backend
```

### Backup Strategy

1. **Database**: Daily automated backups (Azure PostgreSQL)
2. **Blob Storage**: Enable soft delete and versioning
3. **Search Index**: Export configuration and data periodically

### Cost Optimization

After the initial cleanup phase:

1. **Downscale Azure AI Search**: Move to Basic tier
2. **Reduce Container replicas**: Scale down to 1-2 instances
3. **Archive old documents**: Move to Cool storage tier
4. **Pause development resources**: Stop non-production environments

## Troubleshooting

### Common Issues

**Issue**: Database connection errors
- **Solution**: Check DATABASE_URL format and network rules

**Issue**: Azure OpenAI rate limits
- **Solution**: Implement retry logic and request throttling

**Issue**: Vector search not working
- **Solution**: Verify index creation and embedding dimensions

**Issue**: Document parsing failures
- **Solution**: Check file formats and OCR dependencies

### Support

For issues and questions:
- Check logs: `docker-compose logs`
- Review API docs: `http://localhost:8000/docs`
- Contact DevOps team

## Security Checklist

- [ ] All secrets stored in Azure Key Vault
- [ ] Network security groups configured
- [ ] HTTPS enforced on all endpoints
- [ ] CORS properly configured
- [ ] Azure AD authentication enabled
- [ ] Database connection encrypted
- [ ] Blob storage private access only
- [ ] Application Insights configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented
