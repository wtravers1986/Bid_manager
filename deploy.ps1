# Deployment Script for AI Lifting Document Cleanup Tool
# This script checks prerequisites and starts the Docker Compose services

Write-Host "🚀 Starting deployment..." -ForegroundColor Cyan

# Check if Docker is installed
Write-Host "`n📦 Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
Write-Host "`n🔍 Checking if Docker Desktop is running..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker Desktop is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Desktop is not running!" -ForegroundColor Red
    Write-Host "`nPlease start Docker Desktop and wait for it to fully initialize, then run this script again." -ForegroundColor Yellow
    Write-Host "You can start Docker Desktop from the Start menu or by running: Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
Write-Host "`n📝 Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path .env) {
    Write-Host "✅ .env file found" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path env.template) {
        Copy-Item env.template .env
        Write-Host "✅ Created .env file from template" -ForegroundColor Green
        Write-Host "⚠️  IMPORTANT: Please edit .env file and add your Azure OpenAI credentials before continuing!" -ForegroundColor Red
        Write-Host "   Required variables:" -ForegroundColor Yellow
        Write-Host "   - AZURE_OPENAI_ENDPOINT" -ForegroundColor Yellow
        Write-Host "   - AZURE_OPENAI_API_KEY" -ForegroundColor Yellow
        Write-Host "   - AZURE_OPENAI_DEPLOYMENT_NAME" -ForegroundColor Yellow
        Write-Host "   - AZURE_OPENAI_EMBEDDING_DEPLOYMENT" -ForegroundColor Yellow
        $continue = Read-Host "`nPress Enter to continue after editing .env, or Ctrl+C to cancel"
    } else {
        Write-Host "❌ env.template not found. Cannot create .env file." -ForegroundColor Red
        exit 1
    }
}

# Check if data directory exists
Write-Host "`n📁 Checking data directory..." -ForegroundColor Yellow
if (-not (Test-Path data)) {
    Write-Host "📁 Creating data directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path data | Out-Null
    Write-Host "✅ Created data directory" -ForegroundColor Green
} else {
    Write-Host "✅ Data directory exists" -ForegroundColor Green
}

# Stop any existing containers
Write-Host "`n🛑 Stopping any existing containers..." -ForegroundColor Yellow
docker compose down 2>&1 | Out-Null

# Start Docker Compose services
Write-Host "`n🚀 Starting Docker Compose services..." -ForegroundColor Cyan
Write-Host "This may take a few minutes on first run (downloading images)..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Services started successfully!" -ForegroundColor Green
    
    # Wait a bit for services to initialize
    Write-Host "`n⏳ Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check service status
    Write-Host "`n📊 Service Status:" -ForegroundColor Cyan
    docker compose ps
    
    Write-Host "`n🌐 Application URLs:" -ForegroundColor Cyan
    Write-Host "   🎨 Streamlit Frontend: http://localhost:8501" -ForegroundColor Green
    Write-Host "   🔧 Backend API:        http://localhost:8000" -ForegroundColor Green
    Write-Host "   📚 API Documentation:  http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "   ❤️  Health Check:        http://localhost:8000/health" -ForegroundColor Green
    
    Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Open http://localhost:8501 in your browser" -ForegroundColor Yellow
    Write-Host "   2. Go to the 'Index Documents' tab" -ForegroundColor Yellow
    Write-Host "   3. Place PDF/DOCX files in the ./data folder" -ForegroundColor Yellow
    Write-Host "   4. Click 'Index All Documents'" -ForegroundColor Yellow
    
    Write-Host "`n💡 Useful commands:" -ForegroundColor Cyan
    Write-Host "   View logs:        docker compose logs -f" -ForegroundColor Yellow
    Write-Host "   Stop services:    docker compose down" -ForegroundColor Yellow
    Write-Host "   Restart services: docker compose restart" -ForegroundColor Yellow
    
} else {
    Write-Host "`n❌ Failed to start services. Check the error messages above." -ForegroundColor Red
    Write-Host "`nCommon issues:" -ForegroundColor Yellow
    Write-Host "   - Docker Desktop not running" -ForegroundColor Yellow
    Write-Host "   - Ports 5432, 6379, 8000, or 8501 already in use" -ForegroundColor Yellow
    Write-Host "   - Missing or invalid .env configuration" -ForegroundColor Yellow
    Write-Host "`nView logs: docker compose logs" -ForegroundColor Yellow
    exit 1
}










