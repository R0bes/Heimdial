#!/bin/bash
# Linux Script zum Bot stoppen

echo "⏹️  Stopping Bot..."

if [ -f bot/bot.pid ]; then
    PID=$(cat bot/bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 Stopping bot (PID: $PID)..."
        kill $PID
        sleep 1
        echo "✅ Bot stopped successfully"
    else
        echo "⚠️  Bot process not found (PID: $PID)"
    fi
    rm -f bot/bot.pid
else
    echo "ℹ️  No bot.pid file found. Bot might not be running."
fi

