# PowerShell script to create .env file from template
# Run this script: .\setup-env.ps1

$envExamplePath = Join-Path $PSScriptRoot ".env.example"
$envPath = Join-Path $PSScriptRoot ".env"

if (Test-Path $envPath) {
    Write-Host ".env file already exists at: $envPath"
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Skipping .env file creation."
        exit
    }
}

if (Test-Path $envExamplePath) {
    Copy-Item $envExamplePath $envPath
    Write-Host "Created .env file from .env.example at: $envPath"
    Write-Host ""
    Write-Host "IMPORTANT: Please update the following in your .env file:"
    Write-Host "  - VERTEX_AI_PROJECT: Set to your Google Cloud Project ID"
    Write-Host "  - VERTEX_AI_LOCATION: Set to your preferred region (default: us-central1)"
    Write-Host "  - VERTEX_AI_CREDENTIALS_PATH: Optional - path to service account JSON file"
    Write-Host ""
} else {
    Write-Host "Error: .env.example file not found at: $envExamplePath"
    Write-Host "Creating a new .env file with default values..."
    
    $envContent = @"
# Vertex AI Configuration
# Required: Google Cloud Project ID
VERTEX_AI_PROJECT=your-gcp-project-id

# Optional: Vertex AI region (default: us-central1)
VERTEX_AI_LOCATION=us-central1

# Optional: Path to service account JSON file
# If not provided, will use default Google Cloud credentials (ADC)
# VERTEX_AI_CREDENTIALS_PATH=/path/to/service-account-key.json

# Application Settings
APP_NAME=Chatbot
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000

# AI Configuration
TEMPERATURE=0.7
MAX_TOKENS=2000
"@
    
    Set-Content -Path $envPath -Value $envContent
    Write-Host "Created .env file at: $envPath"
    Write-Host ""
    Write-Host "IMPORTANT: Please update VERTEX_AI_PROJECT with your Google Cloud Project ID"
}

