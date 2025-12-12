# 🚀 Quick Start Checkliste

## Was funktioniert automatisch (ohne Runner):

### ✅ GitHub Pages (Mini App)
- **Läuft automatisch** auf GitHub Servern
- **Braucht:** Nur Aktivierung in Settings → Pages
- **Workflow:** `.github/workflows/deploy-pages.yml` (läuft automatisch bei Push)

## Was du noch machen musst:

### 1. 📱 Bot Token & User ID holen
- [ ] Bot bei [@BotFather](https://t.me/botfather) erstellen → Token kopieren
- [ ] User ID bei [@userinfobot](https://t.me/userinfobot) holen

### 2. 🌐 GitHub Pages aktivieren
- [ ] Auf GitHub: **Settings → Pages**
- [ ] Source: **GitHub Actions** wählen
- [ ] Save
- [ ] Warte 2-3 Minuten, dann ist die URL verfügbar: `https://USERNAME.github.io/Heimdial/`

### 3. 🔐 GitHub Secrets setzen (für automatisches Deployment mit Runner)
- [ ] Auf GitHub: **Settings → Secrets and variables → Actions**
- [ ] `BOT_TOKEN` erstellen (dein Bot Token)
- [ ] `ALLOWED_USER_IDS` erstellen (Format: `[123456789]`)
- [ ] `WEBAPP_URL` erstellen (deine GitHub Pages URL)

### 4. 🤖 Bot zum Laufen bringen

**Wähle EINE Option:**

#### Option A: Mit Runner (automatisch) ⚙️
- [ ] Runner auf Windows installieren (siehe README Abschnitt 6.1)
- [ ] Runner als Service starten
- [ ] Fertig! Bei jedem Push wird der Bot automatisch neu gestartet

#### Option B: Ohne Runner (manuell) 🖐️
- [ ] `.env` Datei erstellen (kopiere `env.example` zu `.env` und fülle aus):
  ```env
  BOT_TOKEN=dein_token_hier
  ALLOWED_USER_IDS=[123456789]
  WEBAPP_URL=https://USERNAME.github.io/Heimdial/
  ```
- [ ] Bot starten:
  ```powershell
  # Windows - Einfach starten
  .\start.ps1
  
  # Oder: Mit git pull (nach Code-Änderungen)
  .\deploy.ps1
  
  # Bot stoppen
  .\stop.ps1
  ```
  ```bash
  # Linux - Scripts ausführbar machen (einmalig)
  chmod +x *.sh
  
  # Einfach starten
  ./start.sh
  
  # Oder: Mit git pull (nach Code-Änderungen)
  ./deploy.sh
  
  # Bot stoppen
  ./stop.sh
  ```
- [ ] Nach jedem Code-Update: `.\deploy.ps1` (Windows) oder `./deploy.sh` (Linux) ausführen

### 5. ✅ Testen
- [ ] Telegram öffnen
- [ ] Bot suchen und `/start` senden
- [ ] Auf "🚀 Open Control Panel" klicken
- [ ] Mini App sollte sich öffnen
- [ ] Einen Command testen (z.B. "🖥️ System Info")

## Zusammenfassung:

| Komponente | Läuft auf | Braucht Runner? | Automatisch? |
|------------|-----------|-----------------|--------------|
| **GitHub Pages** | GitHub Servern | ❌ Nein | ✅ Ja (nach Aktivierung) |
| **Bot** | Dein PC | ⚠️ Optional | ⚠️ Nur mit Runner |

**Minimal Setup (ohne Runner):**
1. GitHub Pages aktivieren
2. `.env` erstellen
3. `.\deploy.ps1` ausführen
4. Fertig! ✅

**Vollautomatisch (mit Runner):**
1. GitHub Pages aktivieren
2. GitHub Secrets setzen
3. Runner installieren & starten
4. Fertig! ✅ (danach alles automatisch)

