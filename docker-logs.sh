#!/bin/bash
# Docker Logs Script für Linux
# Zeigt die Bot-Logs an

echo "📋 Bot Logs (Press Ctrl+C to exit):"
docker-compose logs -f bot

