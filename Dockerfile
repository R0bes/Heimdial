FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Utilities installieren (für Commands)
RUN apt-get update && apt-get install -y \
    procps \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Neofetch manuell installieren (nicht im Debian Repo)
RUN curl -L https://raw.githubusercontent.com/dylanaraps/neofetch/master/neofetch -o /usr/local/bin/neofetch && \
    chmod +x /usr/local/bin/neofetch || echo "neofetch installation failed, will use alternative"

# lm-sensors optional (nur wenn verfügbar)
RUN apt-get update && apt-get install -y lm-sensors 2>/dev/null || echo "lm-sensors not available" && \
    rm -rf /var/lib/apt/lists/*

# Bot-Dependencies kopieren und installieren
COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot-Code kopieren
COPY bot/ ./bot/

# Log-Verzeichnis erstellen
RUN mkdir -p /app/logs

# Environment Variables (werden beim Start überschrieben)
ENV BOT_TOKEN=""
ENV ALLOWED_USER_IDS="[]"
ENV WEBAPP_URL=""
ENV DOCKER_CONTAINER="true"

# Bot starten
WORKDIR /app/bot

# Development Mode mit Hot Reload (wenn DOCKER_DEV=true)
# Production Mode (Standard)
CMD if [ "$DOCKER_DEV" = "true" ]; then python bot_dev.py; else python bot.py; fi

