# Telegram PC Control Bot

Telegram Bot mit Mini App zur Remote-Steuerung deines PCs via CI/CD.

## Features

- 🖥️ System Info (neofetch)
- 💾 Disk Space
- 🔄 Uptime
- 📊 Top Prozesse
- 🌡️ CPU Temperature
- 🧠 Memory Usage
- 🏠 Host Info (Hostname & IP)
- 📋 Bot Logs
- 💻 Custom Shell Commands

## Architektur

- **Mini App**: GitHub Pages (automatisch deployed)
- **Bot**: Läuft auf deinem PC
  - **Option 1**: Mit GitHub Actions Runner (automatisches Deployment)
  - **Option 2**: Manuelles Deployment (einfacher, ohne Runner)

## Quick Start

Siehe [QUICKSTART.md](QUICKSTART.md) für eine schnelle Checkliste!

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
| `WEBAPP_URL` | GitHub Pages URL | `https://USERNAME.github.io/Heimdial/` |

**Wichtig:** 
- `ALLOWED_USER_IDS` muss ein JSON Array sein: `[123456789]`
- `WEBAPP_URL` mit **deinem** GitHub Username anpassen

### 5. GitHub Pages aktivieren

**Detaillierte Anleitung:** Siehe [GITHUB_PAGES_SETUP.md](GITHUB_PAGES_SETUP.md)

**Kurzfassung:**
1. Gehe zu: **Settings → Pages** (im Repository)
2. Unter **Source**: Wähle **GitHub Actions** aus dem Dropdown
3. Klicke auf **Save**
4. Fertig! 🎉 (Warte 2-3 Minuten, dann ist die Seite live)

### 6. Bot Deployment

Du hast zwei Optionen:

#### Option A: Manuelles Deployment (Einfacher, ohne Runner)

**1. Environment Variables konfigurieren:**

Erstelle eine `.env` Datei im Projekt-Root:
```env
BOT_TOKEN=dein_bot_token_hier
ALLOWED_USER_IDS=[123456789]
WEBAPP_URL=https://USERNAME.github.io/Heimdial/
```

**2. Bot starten:**

**Windows:**
```powershell
# Einfach starten (ohne git pull)
.\start.ps1

# Oder: Deployment mit git pull
.\deploy.ps1

# Bot stoppen
.\stop.ps1
```

**Linux:**
```bash
# Scripts ausführbar machen (einmalig)
chmod +x *.sh

# Einfach starten (ohne git pull)
./start.sh

# Oder: Deployment mit git pull
./deploy.sh

# Bot stoppen
./stop.sh
```

**Scripts:**
- `start.ps1` / `start.sh`: Startet den Bot (ohne git pull)
- `stop.ps1` / `stop.sh`: Stoppt den Bot
- `deploy.ps1` / `deploy.sh`: Stoppt Bot, pulled Code, installiert Dependencies, startet neu

**Nach jedem Code-Update:** `.\deploy.ps1` (Windows) oder `./deploy.sh` (Linux) ausführen.

**Alternative:** Environment Variables direkt in der Shell setzen (ohne .env Datei):
- Windows: `$env:BOT_TOKEN = "..."` etc.
- Linux: `export BOT_TOKEN="..."` etc.

#### Option B: Automatisches Deployment (Mit GitHub Actions Runner)

### 6. Self-Hosted Runner einrichten (auf deinem PC)

#### Windows

##### 6.1.1 Runner installieren (Windows)

```powershell
# Runner Verzeichnis erstellen
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\actions-runner"
cd "$env:USERPROFILE\actions-runner"

# Runner herunterladen (Windows x64)
Invoke-WebRequest -Uri "https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-win-x64-2.311.0.zip" -OutFile "actions-runner-win-x64-2.311.0.zip"

# Entpacken
Expand-Archive -Path "actions-runner-win-x64-2.311.0.zip" -DestinationPath .
```

##### 6.1.2 Token von GitHub holen (Windows)

1. Gehe zu: **Settings → Actions → Runners**
2. Klicke **New self-hosted runner**
3. Wähle: **Windows** und **x64**
4. Kopiere den **Token** aus dem Configure-Befehl

##### 6.1.3 Runner konfigurieren (Windows)

```powershell
# In $env:USERPROFILE\actions-runner
.\config.cmd --url https://github.com/USERNAME/Heimdial --token DEIN_GITHUB_TOKEN

# Fragen beantworten:
# - Runner group: Default
# - Runner name: [Enter für default]
# - Work folder: [Enter für default]
```

##### 6.1.4 Runner starten (Windows)

**Temporär (für Tests):**
```powershell
.\run.cmd
```

**Permanent (als Windows Service):**
```powershell
# Service installieren (als Administrator)
.\svc.cmd install

# Service starten
.\svc.cmd start

# Status prüfen
.\svc.cmd status

# Bei Bedarf stoppen
.\svc.cmd stop
```

**Wichtig:** Für die Service-Installation benötigst du Administrator-Rechte. Öffne PowerShell als Administrator.

#### Linux

##### 6.2.1 Runner installieren (Linux)

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

##### 6.2.2 Token von GitHub holen (Linux)

1. Gehe zu: **Settings → Actions → Runners**
2. Klicke **New self-hosted runner**
3. Wähle: **Linux** und **x64**
4. Kopiere den **Token** aus dem Configure-Befehl

##### 6.2.3 Runner konfigurieren (Linux)

```bash
# In ~/actions-runner
./config.sh --url https://github.com/USERNAME/Heimdial --token DEIN_GITHUB_TOKEN

# Fragen beantworten:
# - Runner group: Default
# - Runner name: [Enter für default]
# - Work folder: [Enter für default]
```

##### 6.2.4 Runner starten (Linux)

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

### 7. Deployment testen (nur mit Runner)

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

**Windows:**
```powershell
# Auf deinem PC (wo Runner läuft)
cd "$env:USERPROFILE\actions-runner\_work\Heimdial\Heimdial\bot"
Get-Content bot.log
```

**Linux:**
```bash
# Auf deinem PC (wo Runner läuft)
cd ~/actions-runner/_work/Heimdial/Heimdial/bot
cat bot.log
```

### WebApp lädt nicht

- Prüfe ob GitHub Pages aktiv ist: Settings → Pages
- URL korrekt in `WEBAPP_URL` Secret?
- Warte 2-3 Minuten nach erstem Push

### Runner offline

**Windows:**
```powershell
# Status prüfen
cd "$env:USERPROFILE\actions-runner"
.\svc.cmd status

# Neu starten
.\svc.cmd restart
```

**Linux:**
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
