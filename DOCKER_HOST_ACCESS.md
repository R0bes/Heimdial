# Docker Host Access

Dieses Dokument erklärt, wie der Bot Commands auf dem Host-System ausführen kann, obwohl er in einem Docker Container läuft.

## Konfiguration

Die `docker-compose.yml` ist so konfiguriert, dass der Container Zugriff auf das Host-System hat:

### Gemountete Volumes

1. **Docker Socket** (`/var/run/docker.sock`)
   - Ermöglicht Docker Commands vom Container aus
   - Read-only gemountet für Sicherheit

2. **System-Informationen** (`/proc`, `/sys`, `/dev`)
   - Gemountet unter `/host/proc`, `/host/sys`, `/host/dev`
   - Read-only für Sicherheit
   - Ermöglicht Zugriff auf Host-System-Informationen

3. **Root Filesystem** (`/`)
   - Gemountet unter `/host` (read-only)
   - Ermöglicht `df -h` auf Host-Disks

### Capabilities

- `SYS_ADMIN`: Für erweiterte System-Operationen
- `SYS_TIME`: Für Zeit-bezogene Operationen

## Funktionsweise

Der Bot erkennt automatisch, ob er im Container läuft und ob Host-Mounts verfügbar sind:

```python
IN_CONTAINER = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER')
HOST_MOUNTED = os.path.exists('/host/proc') or os.path.exists('/host')
```

Wenn beide Bedingungen erfüllt sind, nutzt der Bot die gemounteten Host-Pfade für Commands:

- `disk_space`: `df -h /host` zeigt Host-Disks
- `system_info`: Liest aus `/host/proc/version`, `/host/proc/cpuinfo`
- `uptime`: Liest aus `/host/proc/uptime`
- `memory`: Liest aus `/host/proc/meminfo`

## Sicherheitshinweise

⚠️ **WICHTIG**: Diese Konfiguration gibt dem Container erweiterten Zugriff auf das Host-System.

- Der Container hat read-only Zugriff auf System-Informationen
- Docker Socket ist read-only gemountet
- Capabilities sind auf das Minimum beschränkt

**Empfehlungen:**
- Nutze diese Konfiguration nur in vertrauenswürdigen Umgebungen
- Prüfe regelmäßig die Container-Logs
- Verwende keine `privileged: true` Mode (ist auskommentiert)
- Beschränke den Zugriff auf autorisierte User über `ALLOWED_USER_IDS`

## Alternative: Ohne Host-Zugriff

Wenn du den Bot ohne Host-Zugriff betreiben möchtest, entferne die folgenden Zeilen aus `docker-compose.yml`:

```yaml
# Entfernen:
- /var/run/docker.sock:/var/run/docker.sock:ro
- /proc:/host/proc:ro
- /sys:/host/sys:ro
- /dev:/host/dev:ro
- /:/host:ro
cap_add:
  - SYS_ADMIN
  - SYS_TIME
```

Der Bot wird dann nur Container-spezifische Informationen anzeigen.

