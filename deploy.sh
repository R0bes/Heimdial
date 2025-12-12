#!/bin/bash
# Linux Deployment Script
# Stoppt den Bot, pulled den neuesten Code und startet den Bot neu

echo "🔄 Deploying Bot..."

# Bot stoppen
if [ -f bot/bot.pid ]; then
    PID=$(cat bot/bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⏹️  Stopping bot (PID: $PID)..."
        kill $PID
        sleep 2
    fi
    rm -f bot/bot.pid
fi

# Git pull
echo "📥 Pulling latest code..."
git pull

# Dependencies installieren
echo "📦 Installing dependencies..."
cd bot
pip install -r requirements.txt

# Environment Variables laden (falls .env existiert)
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Bot starten
echo "🚀 Starting bot..."
nohup python bot.py > bot.log 2>&1 &
echo $! > bot.pid

sleep 2

# Verifizieren
PID=$(cat bot.pid)
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Bot deployed successfully! (PID: $PID)"
else
    echo "❌ Bot failed to start. Check bot.log"
    cat bot.log
    exit 1
fi

cd ..

