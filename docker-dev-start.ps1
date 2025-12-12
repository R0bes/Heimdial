# Development Mode: Startet Bot mit Hot Reload
$env:DOCKER_DEV = "true"
docker-compose up -d
Write-Host "🔥 Development Mode aktiviert - Hot Reload aktiv"
Write-Host "📂 Code-Änderungen werden automatisch geladen"
Write-Host ""
Write-Host "Logs ansehen:"
Write-Host "  docker-compose logs -f bot"
Write-Host ""
Write-Host "Production Mode:"
Write-Host "  \$env:DOCKER_DEV = 'false'"
Write-Host "  docker-compose restart bot"

