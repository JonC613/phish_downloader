#!/bin/bash
# Startup script for Phish Downloader Docker environment

set -e

echo "🎸 Starting Phish Downloader Docker Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

echo "📊 Loading database..."
docker-compose up db_loader

echo "🌐 Starting Streamlit app..."
docker-compose up -d streamlit

echo ""
echo "✅ All services started successfully!"
echo ""
echo "🌐 Streamlit UI: http://localhost:8501"
echo "🐘 PostgreSQL: localhost:5434"
echo ""
echo "To view logs: docker-compose logs -f streamlit"
echo "To stop: docker-compose down"
echo "To stop and remove data: docker-compose down -v"
