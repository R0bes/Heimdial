#!/bin/bash
# Development Mode: Startet Bot mit Hot Reload
export DOCKER_DEV=true
docker-compose up -d
echo "🔥 Development Mode aktiviert - Hot Reload aktiv"
echo "📂 Code-Änderungen werden automatisch geladen"
echo ""
echo "Logs ansehen:"
echo "  docker-compose logs -f bot"
echo ""
echo "Production Mode:"
echo "  export DOCKER_DEV=false"
echo "  docker-compose restart bot"

