#!/bin/bash
# Docker Start Script für Linux
# Startet den Bot in einem Docker Container

echo "🐳 Starting Bot in Docker..."

# Prüfen ob Docker läuft
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "   Please start Docker first"
    exit 1
fi

# Prüfen ob .env existiert
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Please create .env file with BOT_TOKEN, ALLOWED_USER_IDS, and WEBAPP_URL"
    exit 1
fi

# Logs-Verzeichnis erstellen
mkdir -p logs

# Container stoppen falls er läuft
echo "🛑 Stopping existing container..."
docker-compose down 2>&1 > /dev/null

# Container bauen und starten
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting container..."
docker-compose up -d

sleep 2

# Status prüfen
if docker-compose ps | grep -q "heimdial-bot.*Up"; then
    echo "✅ Bot started successfully in Docker!"
    echo "📋 View logs: docker-compose logs -f"
    echo "🛑 Stop: docker-compose down"
else
    echo "❌ Bot failed to start. Check logs:"
    echo "   docker-compose logs"
    exit 1
fi

