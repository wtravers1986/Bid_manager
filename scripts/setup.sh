#!/bin/bash
# Setup script for AI Lifting Document Cleanup Tool

set -e

echo "🚀 Setting up AI Lifting Document Cleanup Tool..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }

echo "✅ Prerequisites check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp backend/.env.example .env
    echo "⚠️  Please edit .env file with your Azure credentials before starting the application"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads output logs

# Pull Docker images
echo "🐳 Pulling Docker images..."
docker-compose pull

# Build custom images
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Azure credentials"
echo "2. Run: docker-compose up -d"
echo "3. Access the application at http://localhost:8000"
echo "4. API documentation at http://localhost:8000/docs"
echo ""
