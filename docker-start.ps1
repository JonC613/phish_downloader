# PowerShell script to start Phish Downloader Docker environment

Write-Host "🎸 Starting Phish Downloader Docker Environment..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Build and start services
Write-Host "`n📦 Building Docker images..." -ForegroundColor Yellow
docker-compose build

Write-Host "`n🚀 Starting PostgreSQL..." -ForegroundColor Yellow
docker-compose up -d postgres

Write-Host "`n⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`n📊 Loading database..." -ForegroundColor Yellow
docker-compose up db_loader

Write-Host "`n🌐 Starting Streamlit app..." -ForegroundColor Yellow
docker-compose up -d streamlit

Write-Host "`n✅ All services started successfully!" -ForegroundColor Green
Write-Host "`n🌐 Streamlit UI: " -NoNewline
Write-Host "http://localhost:8501" -ForegroundColor Cyan
Write-Host "🐘 PostgreSQL: " -NoNewline
Write-Host "localhost:5434" -ForegroundColor Cyan
Write-Host "`nUseful commands:"
Write-Host "  View logs: " -NoNewline
Write-Host "docker-compose logs -f streamlit" -ForegroundColor Yellow
Write-Host "  Stop: " -NoNewline
Write-Host "docker-compose down" -ForegroundColor Yellow
Write-Host "  Stop and remove data: " -NoNewline
Write-Host "docker-compose down -v" -ForegroundColor Yellow
