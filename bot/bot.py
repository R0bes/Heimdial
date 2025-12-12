import os
import json
import subprocess
import sys
import platform
import socket
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging konfigurieren (wird in main() überschrieben, aber hier initialisiert)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_IDS = json.loads(os.getenv("ALLOWED_USER_IDS", "[]"))
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

# Helper class for fake subprocess result
class FakeResult:
    def __init__(self, stdout, stderr='', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

# Predefined Commands (platform-specific)
if IS_WINDOWS:
    COMMANDS = {
        'host_info': 'hostname && ipconfig | findstr IPv4',
        'system_info': 'systeminfo',
        'disk_space': 'wmic logicaldisk get size,freespace,caption',
        'uptime': 'net stats srv',
        'processes': 'tasklist /FO TABLE /SORT:CPU',
        'temp': 'wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature',
        'memory': 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list',
        'bot_logs': 'Get-Content bot.log -Tail 50 -ErrorAction SilentlyContinue'
    }
else:
    COMMANDS = {
        'host_info': 'hostname && hostname -I',
        'system_info': 'neofetch 2>/dev/null || (echo "=== System Info ===" && uname -a && echo "" && cat /etc/os-release)',
        'disk_space': 'df -h',
        'uptime': 'uptime',
        'processes': 'ps aux --sort=-%cpu | head -15',
        'temp': 'sensors 2>/dev/null || echo "sensors not available"',
        'memory': 'free -h',
        'bot_logs': 'tail -50 /app/bot/bot.log 2>/dev/null || tail -50 bot.log 2>/dev/null || echo "No log file found. Bot is running in Docker. Use: docker-compose logs bot"'
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für /start Command"""
    logger = logging.getLogger(__name__)
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("❌ Unauthorized")
        logger.warning(f"⚠️  Unauthorized access attempt from User ID: {user_id} (@{username})")
        return
    
    logger.info(f"✅ /start command from User ID: {user_id} (@{username})")
    
    # Host-Informationen sammeln
    hostname = socket.gethostname()
    
    # Prüfe ob wir in Docker/WSL2 laufen
    is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER')
    is_wsl = 'microsoft' in platform.release().lower() or 'WSL' in platform.release()
    
    try:
        # Versuche lokale IP zu bekommen
        if IS_WINDOWS:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
            ip_lines = [line.strip() for line in result.stdout.split('\n') if 'IPv4' in line]
            local_ip = ip_lines[0].split(':')[-1].strip() if ip_lines else "N/A"
        else:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            local_ip = result.stdout.strip().split()[0] if result.stdout.strip() else "N/A"
    except:
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "N/A"
    
    os_name = platform.system()
    os_release = platform.release()
    
    # Versuche Windows-Hostname zu bekommen (wenn in WSL2)
    windows_hostname = None
    if is_wsl and not IS_WINDOWS:
        try:
            # WSL2: Windows-Hostname über /etc/hostname oder hostname.exe
            result = subprocess.run(['hostname.exe'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                windows_hostname = result.stdout.strip()
        except:
            pass
    
    keyboard = [
        [InlineKeyboardButton("🚀 Open Control Panel", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Host-Info zusammenstellen
    host_info_parts = [f"🖥️ Host: {hostname}"]
    if windows_hostname:
        host_info_parts.append(f"🪟 Windows Host: {windows_hostname}")
    if is_docker:
        host_info_parts.append("🐳 Container: Docker")
    if is_wsl:
        host_info_parts.append("🐧 Environment: WSL2")
    host_info_parts.append(f"💻 OS: {os_name} {os_release}")
    host_info_parts.append(f"🌐 IP: {local_ip}")
    
    host_info = "\n".join(host_info_parts)
    
    await update.message.reply_text(
        f"✅ Bot aktiv!\nUser ID: {user_id}\n\n{host_info}\n\nÖffne das Control Panel:",
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für WebApp Data (Commands von Mini App)"""
    logger = logging.getLogger(__name__)
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    
    if user_id not in ALLOWED_USER_IDS:
        logger.warning(f"⚠️  Unauthorized WebApp access from User ID: {user_id} (@{username})")
        return
    
    try:
        logger.info(f"📱 WebApp data received from User ID: {user_id} (@{username})")
        # Parse WebApp Data
        data = json.loads(update.effective_message.web_app_data.data)
        cmd_key = data.get('command')
        
        # Bestimme Command
        if cmd_key == 'custom':
            cmd = data.get('custom_cmd', '')
        else:
            cmd = COMMANDS.get(cmd_key, '')
        
        if not cmd:
            await update.message.reply_text("❌ Unknown command")
            return
        
        # Feedback an User
        logger.info(f"⚙️  Executing command '{cmd_key}' from User ID: {user_id} (@{username})")
        logger.debug(f"Command: {cmd[:100]}...")
        await update.message.reply_text(f"⚙️ Running: `{cmd}`", parse_mode="Markdown")
        
        # Spezialbehandlung für bot_logs
        if cmd_key == 'bot_logs':
            # Prüfe ob wir in Docker laufen
            if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
                # In Docker: Log-Datei direkt lesen
                log_paths = ['/app/bot/bot.log', 'bot.log', '/app/logs/bot.log']
                output = None
                for log_path in log_paths:
                    if os.path.exists(log_path):
                        try:
                            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = f.readlines()
                                output = ''.join(lines[-50:]) if len(lines) > 50 else ''.join(lines)
                                break
                        except:
                            continue
                
                # Simuliere subprocess result
                if output:
                    result = FakeResult(output)
                else:
                    result = FakeResult('📋 Bot is running in Docker.\n\nTo view logs, use:\n  docker-compose logs -f bot\n\nOr check the logs directory.')
            elif IS_WINDOWS:
                # PowerShell Command direkt ausführen
                result = subprocess.run(
                    ['powershell', '-Command', cmd],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
            else:
                # Linux: Command ausführen
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
        else:
            # Command ausführen
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        
        # Output zusammenstellen
        output = result.stdout if result.stdout else result.stderr
        if not output and cmd_key == 'bot_logs':
            output = "📋 No log entries yet. Bot is running."
        output = output[:4000] if output else "✅ Done (no output)"
        
        # Ergebnis senden
        logger.info(f"✅ Command '{cmd_key}' completed successfully")
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")
        
    except subprocess.TimeoutExpired:
        logger.warning(f"⏱️  Command '{cmd_key}' timed out after 30s")
        await update.message.reply_text("❌ Timeout (>30s)")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"❌ Command execution error: {e}", exc_info=True)

def main():
    """Main Function"""
    # Logging konfigurieren (muss vor Validierung sein)
    import sys
    import io
    
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.log')
    
    # Root Logger konfigurieren - entferne alle vorhandenen Handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    # Entferne alle vorhandenen Handler, um doppelte Logs zu vermeiden
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler für Datei (alle Logs)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    
    # Handler für Console (nur INFO und höher, ohne Telegram/httpx Spam)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Farb-Formatter für Console
    class ColoredFormatter(logging.Formatter):
        """Formatter mit Farben für Log-Level"""
        # ANSI Escape Codes für Farben (nur wenn TTY)
        COLORS = {
            'DEBUG': '\033[36m',      # Cyan
            'INFO': '\033[32m',       # Grün
            'WARNING': '\033[33m',    # Gelb
            'ERROR': '\033[31m',      # Rot
            'CRITICAL': '\033[35m',   # Magenta
        }
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        def __init__(self, datefmt=None):
            super().__init__(datefmt=datefmt)
            # Prüfe ob stdout ein TTY ist (für Docker/Container)
            self.use_colors = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        
        def format(self, record):
            # Zeit formatieren (überschreibe asctime mit formatiertem Datum)
            if hasattr(self, 'datefmt') and self.datefmt:
                record.asctime = self.formatTime(record, self.datefmt)
            else:
                record.asctime = self.formatTime(record)
            time_str = record.asctime
            
            # Level-Name mit Farbe stylen
            levelname = record.levelname
            
            # Level-Symbol statt Text
            level_symbols = {
                'DEBUG': '🔍',
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨',
            }
            level_symbol = level_symbols.get(levelname, '•')
            
            # Format: Zeit | Symbol | Nachricht
            # Nur Farben verwenden wenn TTY, sonst nur Symbol
            if self.use_colors and levelname in self.COLORS:
                color = self.COLORS[levelname]
                formatted = f'{time_str} | {color}{self.BOLD}{level_symbol}{self.RESET} | {record.getMessage()}'
            else:
                # Ohne Farben, nur Symbol
                formatted = f'{time_str} | {level_symbol} | {record.getMessage()}'
            
            return formatted
    
    console_formatter = ColoredFormatter(datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # Filter für Console: Telegram/httpx DEBUG/INFO-Logs ausblenden
    class TelegramFilter(logging.Filter):
        def filter(self, record):
            # Telegram und httpx DEBUG/INFO-Logs komplett ausblenden (nur in Datei)
            telegram_loggers = ['httpx', 'telegram', 'httpcore']
            if any(record.name.startswith(logger) for logger in telegram_loggers):
                # Alle DEBUG/INFO-Logs von Telegram/httpx ausblenden
                return False
            return True
    
    console_handler.addFilter(TelegramFilter())
    
    # Handler hinzufügen
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Bot Logger - verhindere Propagation zum Root-Logger, um doppelte Logs zu vermeiden
    bot_logger = logging.getLogger(__name__)
    bot_logger.propagate = False  # Verhindere, dass Logs zum Root-Logger propagieren
    bot_logger.setLevel(logging.DEBUG)
    bot_logger.addHandler(file_handler)
    bot_logger.addHandler(console_handler)
    
    # Telegram/httpx Logger: DEBUG für Datei, aber WARNING für Console
    # Setze die Logger-Level direkt auf WARNING, damit sie nicht in Console erscheinen
    # Die Datei-Handler werden trotzdem alle Logs aufnehmen (DEBUG-Level)
    for logger_name in ['httpx', 'telegram', 'telegram.ext', 'httpcore']:
        logger_obj = logging.getLogger(logger_name)
        # Entferne alle Handler von diesen Loggern
        for handler in logger_obj.handlers[:]:
            logger_obj.removeHandler(handler)
        # Setze Level auf WARNING für Console (DEBUG-Logs werden nicht angezeigt)
        logger_obj.setLevel(logging.WARNING)
        # Füge Datei-Handler hinzu (für vollständige Logs)
        file_handler_telegram = logging.FileHandler(log_file, encoding='utf-8')
        file_handler_telegram.setLevel(logging.DEBUG)  # Alle Logs in Datei
        file_handler_telegram.setFormatter(file_formatter)
        logger_obj.addHandler(file_handler_telegram)
    
    # Bot Logger wird bereits oben konfiguriert
    logger = bot_logger
    
    # UTF-8 Encoding für Windows Console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Validierung
    if not TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        sys.exit(1)
    if not ALLOWED_USER_IDS:
        logger.error("❌ ALLOWED_USER_IDS not set!")
        sys.exit(1)
    if not WEBAPP_URL:
        logger.error("❌ WEBAPP_URL not set!")
        sys.exit(1)
    
    # Application erstellen
    application = Application.builder().token(TOKEN).build()
    
    # Handlers registrieren
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Bot Start Info
    logger.info("=" * 60)
    logger.info("🤖 Bot started successfully")
    logger.info(f"📱 WebApp URL: {WEBAPP_URL}")
    logger.info(f"👥 Allowed Users: {ALLOWED_USER_IDS}")
    logger.info(f"🖥️  Platform: {platform.system()} {platform.release()}")
    logger.info("=" * 60)
    
    # Polling starten
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
