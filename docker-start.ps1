# Docker Start Script für Windows
# Startet den Bot in einem Docker Container

Write-Host "🐳 Starting Bot in Docker..." -ForegroundColor Cyan

# Prüfen ob Docker läuft
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop first" -ForegroundColor Yellow
    exit 1
}

# Prüfen ob .env existiert
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "   Please create .env file with BOT_TOKEN, ALLOWED_USER_IDS, and WEBAPP_URL" -ForegroundColor Yellow
    exit 1
}

# Logs-Verzeichnis erstellen
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Container stoppen falls er läuft
Write-Host "🛑 Stopping existing container..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Container bauen und starten
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan
docker-compose build

Write-Host "🚀 Starting container..." -ForegroundColor Cyan
docker-compose up -d

Start-Sleep -Seconds 2

# Status prüfen
$status = docker-compose ps
if ($status -match "heimdial-bot.*Up") {
    Write-Host "✅ Bot started successfully in Docker!" -ForegroundColor Green
    Write-Host "📋 View logs: docker-compose logs -f" -ForegroundColor Cyan
    Write-Host "🛑 Stop: docker-compose down" -ForegroundColor Cyan
} else {
    Write-Host "❌ Bot failed to start. Check logs:" -ForegroundColor Red
    Write-Host "   docker-compose logs" -ForegroundColor Yellow
    exit 1
}

