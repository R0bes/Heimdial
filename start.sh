#!/bin/bash
# Linux Script zum Bot starten (ohne Deployment)
# Verwendet .env Datei oder Environment Variables

echo "🚀 Starting Bot..."

# Prüfen ob Bot bereits läuft
if [ -f bot/bot.pid ]; then
    PID=$(cat bot/bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Bot is already running (PID: $PID)"
        echo "   Use stop.sh to stop it first, or deploy.sh to restart"
        exit 1
    else
        rm -f bot/bot.pid
    fi
fi

# Environment Variables laden (falls .env existiert)
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  No .env file found. Make sure environment variables are set!"
fi

# Prüfen ob Environment Variables gesetzt sind
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN not set!"
    echo "   Create a .env file or set environment variables"
    exit 1
fi

if [ -z "$ALLOWED_USER_IDS" ]; then
    echo "❌ ALLOWED_USER_IDS not set!"
    exit 1
fi

if [ -z "$WEBAPP_URL" ]; then
    echo "❌ WEBAPP_URL not set!"
    exit 1
fi

# Dependencies prüfen
echo "📦 Checking dependencies..."
cd bot
if ! python -m pip show python-telegram-bot > /dev/null 2>&1; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Bot starten
echo "🤖 Starting bot..."
nohup python bot.py > bot.log 2>&1 &
echo $! > bot.pid

sleep 2

# Verifizieren
PID=$(cat bot.pid)
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Bot started successfully! (PID: $PID)"
    echo "📋 Logs: bot/bot.log"
    echo "🛑 Stop with: ./stop.sh"
else
    echo "❌ Bot failed to start. Check bot.log"
    cat bot.log
    exit 1
fi

cd ..

