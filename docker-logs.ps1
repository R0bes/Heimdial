# Docker Logs Script für Windows
# Zeigt die Bot-Logs an

Write-Host "📋 Bot Logs (Press Ctrl+C to exit):" -ForegroundColor Cyan
docker-compose logs -f bot

