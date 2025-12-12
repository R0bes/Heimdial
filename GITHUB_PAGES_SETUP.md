# 📖 GitHub Pages Setup - Schritt für Schritt

## Schritt-für-Schritt Anleitung

### 1. Gehe zu den Repository Settings
- Öffne dein Repository auf GitHub: `https://github.com/R0bes/Heimdial`
- Klicke auf **Settings** (oben im Menü)

### 2. Gehe zu Pages
- Im linken Menü: Scrolle runter zu **Pages** (unter "Code and automation")
- Oder gehe direkt zu: `https://github.com/R0bes/Heimdial/settings/pages`

### 3. Source auswählen
- Unter **Source** findest du ein Dropdown-Menü
- Wähle: **GitHub Actions** (nicht "Deploy from a branch"!)

### 4. Speichern
- Klicke auf **Save** (Button sollte rechts oben oder unten erscheinen)
- **Das war's!** 🎉

### 5. Was passiert danach?

Nach dem Speichern:
1. GitHub erstellt automatisch ein "github-pages" Environment
2. Beim nächsten Push (oder manuell) wird der Workflow ausgeführt
3. Nach 2-3 Minuten ist deine Seite verfügbar unter:
   - `https://R0bes.github.io/Heimdial/`

### 6. Workflow manuell starten (optional)

Falls du nicht warten willst, bis du etwas pusht:
1. Gehe zu **Actions** Tab
2. Wähle **Deploy GitHub Pages** Workflow
3. Klicke **Run workflow** → **Run workflow**

### 7. Status prüfen

**Workflow Status:**
- Gehe zu **Actions** Tab
- Du solltest "Deploy GitHub Pages" sehen
- Grüner Haken ✅ = Erfolgreich
- Gelbes Symbol ⏳ = Läuft noch
- Roter Haken ❌ = Fehler (dann Logs prüfen)

**Pages Status:**
- Gehe zurück zu **Settings → Pages**
- Du solltest sehen: "Your site is live at https://R0bes.github.io/Heimdial/"

## Troubleshooting

### "GitHub Actions" Option fehlt?
- Stelle sicher, dass der Workflow `.github/workflows/deploy-pages.yml` existiert
- Prüfe, ob du die nötigen Permissions hast (Repository Owner/Admin)

### Workflow läuft nicht?
- Prüfe den **Actions** Tab auf Fehler
- Stelle sicher, dass der Branch `main` heißt (nicht `master`)

### Seite lädt nicht?
- Warte 2-3 Minuten nach dem ersten Deployment
- Prüfe die URL: `https://R0bes.github.io/Heimdial/` (mit `/` am Ende!)
- Öffne die Browser-Konsole (F12) auf Fehler

### 404 Error?
- Prüfe, ob `index.html` im Root-Verzeichnis existiert
- Prüfe die Workflow-Logs im **Actions** Tab

## Nächste Schritte

Sobald GitHub Pages läuft:
1. ✅ URL notieren: `https://R0bes.github.io/Heimdial/`
2. ✅ Diese URL in deiner `.env` Datei eintragen (falls noch nicht geschehen)
3. ✅ Bot in Telegram testen - Mini App sollte sich öffnen!

