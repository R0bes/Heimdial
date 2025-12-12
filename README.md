# Telegram PC Control Bot

Telegram Bot mit Mini App zur Remote-Steuerung deines PCs via CI/CD.

## Features

- 🖥️ System Info (neofetch)
- 💾 Disk Space
- 🔄 Uptime
- 📊 Top Prozesse
- 🌡️ CPU Temperature
- 🧠 Memory Usage
- 💻 Custom Shell Commands

## Architektur

- **Mini App**: GitHub Pages (automatisch deployed)
- **Bot**: Self-Hosted Runner auf deinem PC (automatisch deployed via CI/CD)

## Setup

### 1. Bot erstellen

1. Öffne [@BotFather](https://t.me/botfather) in Telegram
2. Sende `/newbot`
3. Folge den Anweisungen
4. Kopiere den **Bot Token**

### 2. User ID herausfinden

1. Öffne [@userinfobot](https://t.me/userinfobot) in Telegram
2. Starte den Bot
3. Kopiere deine **User ID** (Zahl)

### 3. GitHub Repository

Repository ist bereits erstellt und gepusht.

### 4. GitHub Secrets konfigurieren

Gehe zu: **Settings → Secrets and variables → Actions → New repository secret**

Erstelle folgende Secrets:

| Name | Wert | Beispiel |
|------|------|----------|
| `BOT_TOKEN` | Dein Bot Token von BotFather | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `ALLOWED_USER_IDS` | JSON Array mit deiner User ID | `[123456789]` |
| `WEBAPP_URL` | GitHub Pages URL | `https://USERNAME.github.io/telegram-pc-control/` |

**Wichtig:** 
- `ALLOWED_USER_IDS` muss ein JSON Array sein: `[123456789]`
- `WEBAPP_URL` mit **deinem** GitHub Username anpassen

### 5. GitHub Pages aktivieren

1. Gehe zu: **Settings → Pages**
2. Source: **GitHub Actions**
3. Save

### 6. Self-Hosted Runner einrichten (auf deinem PC)

#### 6.1 Runner installieren

```bash
# Runner Verzeichnis erstellen
mkdir -p ~/actions-runner
cd ~/actions-runner

# Runner herunterladen (Linux x64)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Entpacken
tar xzf actions-runner-linux-x64-2.311.0.tar.gz
```

#### 6.2 Token von GitHub holen

1. Gehe zu: **Settings → Actions → Runners**
2. Klicke **New self-hosted runner**
3. Wähle: **Linux** und **x64**
4. Kopiere den **Token** aus dem Configure-Befehl

#### 6.3 Runner konfigurieren

```bash
# In ~/actions-runner
./config.sh --url https://github.com/USERNAME/telegram-pc-control --token DEIN_GITHUB_TOKEN

# Fragen beantworten:
# - Runner group: Default
# - Runner name: [Enter für default]
# - Work folder: [Enter für default]
```

#### 6.4 Runner starten

**Temporär (für Tests):**
```bash
./run.sh
```

**Permanent (als Service):**
```bash
sudo ./svc.sh install
sudo ./svc.sh start

# Status prüfen
sudo ./svc.sh status

# Bei Bedarf stoppen
sudo ./svc.sh stop
```

### 7. Deployment testen

```bash
# In deinem lokalen Repo
git commit --allow-empty -m "Test deployment"
git push

# Workflows prüfen auf GitHub:
# Actions Tab → Beide Workflows sollten laufen
```

### 8. Bot verwenden

1. Öffne Telegram
2. Suche deinen Bot
3. Sende `/start`
4. Klicke auf "🚀 Open Control Panel"
5. Mini App öffnet sich
6. Commands ausführen

## Workflow

```
Code ändern → git push → GitHub Actions → Bot neu gestartet auf PC
```

## Troubleshooting

### Bot startet nicht

```bash
# Auf deinem PC (wo Runner läuft)
cd ~/actions-runner/_work/telegram-pc-control/telegram-pc-control/bot
cat bot.log
```

### WebApp lädt nicht

- Prüfe ob GitHub Pages aktiv ist: Settings → Pages
- URL korrekt in `WEBAPP_URL` Secret?
- Warte 2-3 Minuten nach erstem Push

### Runner offline

```bash
# Status prüfen
sudo ~/actions-runner/svc.sh status

# Neu starten
sudo ~/actions-runner/svc.sh restart
```

### Unauthorized Error

- User ID korrekt in `ALLOWED_USER_IDS`?
- Format: `[123456789]` (mit eckigen Klammern)

## Sicherheit

- ✅ User-Whitelist aktiviert
- ✅ Command Timeout (30s)
- ✅ Keine Secrets im Code
- ✅ Bot läuft lokal (nicht in Cloud)

## Weitere Commands hinzufügen

### In index.html:

```html
<button onclick="sendCommand('neuer_command')">
    🆕 Neuer Command
</button>
```

### In bot/bot.py:

```python
COMMANDS = {
    # ... bestehende commands
    'neuer_command': 'dein bash command hier'
}
```

Dann: `git commit` und `git push` → Automatisch deployed!
