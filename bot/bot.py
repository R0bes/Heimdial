import os
import json
import subprocess
import sys
import platform
import socket
import logging
import signal
import atexit
import asyncio
import re
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
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

def parse_disk_space(df_output):
    """Parst `df -h` Output und gibt strukturierte JSON-Daten zurück"""
    disks = []
    lines = df_output.strip().split('\n')
    
    # Überspringe Header-Zeile
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # Parse Zeile: Filesystem Size Used Avail Use% Mounted on
        parts = line.split()
        if len(parts) >= 6:
            filesystem = parts[0]
            size_str = parts[1]
            used_str = parts[2]
            avail_str = parts[3]
            use_pct_str = parts[4].rstrip('%')
            mounted_on = ' '.join(parts[5:]) if len(parts) > 5 else ''
            
            # Konvertiere Größen zu Bytes (für Charts)
            def parse_size(size_str):
                """Konvertiert Größen wie '1007G', '74G' zu Bytes"""
                if not size_str or size_str == '-':
                    return 0
                size_str = size_str.upper()
                multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
                for suffix, mult in multipliers.items():
                    if size_str.endswith(suffix):
                        num = float(size_str[:-1])
                        return int(num * mult)
                # Fallback: versuche als Zahl zu parsen
                try:
                    return int(float(size_str))
                except:
                    return 0
            
            size_bytes = parse_size(size_str)
            used_bytes = parse_size(used_str)
            avail_bytes = parse_size(avail_str)
            
            try:
                use_pct = float(use_pct_str)
            except:
                use_pct = 0.0
            
            disks.append({
                'filesystem': filesystem,
                'size': size_str,
                'used': used_str,
                'avail': avail_str,
                'use_percent': use_pct,
                'mounted_on': mounted_on,
                'size_bytes': size_bytes,
                'used_bytes': used_bytes,
                'avail_bytes': avail_bytes
            })
    
    return disks

def get_main_menu_keyboard():
    """Erstellt das Hauptmenü mit Quick Actions als ReplyKeyboard (für WebApp)"""
    keyboard = [
        [
            KeyboardButton("🏠 Host Info"),
            KeyboardButton("🖥️ System Info")
        ],
        [
            KeyboardButton("💾 Disk Space"),
            KeyboardButton("🔄 Uptime")
        ],
        [
            KeyboardButton("📈 Top Prozesse"),
            KeyboardButton("🌡️ Temperature")
        ],
        [
            KeyboardButton("🧠 Memory"),
            KeyboardButton("📋 Bot Logs")
        ],
        # WICHTIG: KeyboardButton für WebApp (nicht InlineKeyboardButton), damit sendData funktioniert
        [KeyboardButton("🚀 Open Control Panel", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_inline_menu_keyboard():
    """Erstellt das Hauptmenü mit Quick Actions als InlineKeyboard (für CallbackQueries)"""
    keyboard = [
        [
            InlineKeyboardButton("🏠 Host Info", callback_data="quick_host_info"),
            InlineKeyboardButton("🖥️ System Info", callback_data="quick_system_info")
        ],
        [
            InlineKeyboardButton("💾 Disk Space", callback_data="quick_disk_space"),
            InlineKeyboardButton("🔄 Uptime", callback_data="quick_uptime")
        ],
        [
            InlineKeyboardButton("📈 Top Prozesse", callback_data="quick_processes"),
            InlineKeyboardButton("🌡️ Temperature", callback_data="quick_temp")
        ],
        [
            InlineKeyboardButton("🧠 Memory", callback_data="quick_memory"),
            InlineKeyboardButton("📋 Bot Logs", callback_data="quick_bot_logs")
        ],
        [InlineKeyboardButton("🚀 Open Control Panel", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    return InlineKeyboardMarkup(keyboard)

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
        'bot_logs': 'Get-Content bot.log -Tail 20 -ErrorAction SilentlyContinue'
    }
else:
    COMMANDS = {
        'host_info': 'hostname && hostname -I',
        'system_info': 'echo "=== System Info ===" && uname -a && echo "" && echo "Uptime:" && uptime -p 2>/dev/null || uptime && echo "" && echo "CPU:" && lscpu | grep "Model name" 2>/dev/null || echo "CPU: N/A" && echo "Memory:" && free -h | head -2',
        'disk_space': 'df -h',
        'uptime': 'uptime',
        'processes': 'ps aux --sort=-%cpu | head -15',
        'temp': 'sensors 2>/dev/null || echo "sensors not available"',
        'memory': 'free -h',
        'bot_logs': 'tail -20 /app/bot/bot.log 2>/dev/null || tail -20 bot.log 2>/dev/null || echo "No log file found. Bot is running in Docker. Use: docker-compose logs bot"'
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für /start Command"""
    logger = logging.getLogger(__name__)
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    
    # Finde Index des Users in ALLOWED_USER_IDS
    try:
        user_index = ALLOWED_USER_IDS.index(user_id)
        match_status = f"Match: User[{user_index}]"
    except ValueError:
        match_status = "No Match"
    
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("❌ Unauthorized")
        logger.warning(f"⚠️  Unauthorized access attempt from User ID: {user_id} (@{username}) - {match_status}")
        return
    
    logger.info(f"✅ /start command from User ID: {user_id} (@{username}) - {match_status}")
    
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
    
    # Quick Actions Buttons (Hauptmenü)
    reply_markup = get_main_menu_keyboard()
    
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
    logger.info("🔔 handle_webapp_data called!")
    
    # Prüfe verschiedene Update-Typen
    if update.message and update.message.web_app_data:
        logger.info(f"📱 WebApp data found in update.message")
        message = update.message
    elif update.effective_message and update.effective_message.web_app_data:
        logger.info(f"📱 WebApp data found in update.effective_message")
        message = update.effective_message
    else:
        logger.error(f"❌ No web_app_data found in update. Update type: {type(update)}")
        logger.error(f"❌ Update has message: {update.message is not None}")
        logger.error(f"❌ Update has effective_message: {update.effective_message is not None}")
        if update.message:
            logger.error(f"❌ Message has web_app_data: {hasattr(update.message, 'web_app_data')}")
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    
    # Finde Index des Users in ALLOWED_USER_IDS
    try:
        user_index = ALLOWED_USER_IDS.index(user_id)
        match_status = f"Match: User[{user_index}]"
    except ValueError:
        match_status = "No Match"
    
    if user_id not in ALLOWED_USER_IDS:
        logger.warning(f"⚠️  Unauthorized WebApp access from User ID: {user_id} (@{username}) - {match_status}")
        return
    
    try:
        logger.info(f"📱 WebApp data received from User ID: {user_id} (@{username}) - {match_status}")
        
        # Parse WebApp Data
        web_app_data = message.web_app_data
        logger.info(f"📱 Raw WebApp data: {web_app_data.data}")
        data = json.loads(web_app_data.data)
        logger.info(f"📱 Parsed WebApp data: {data}")
        cmd_key = data.get('command')
        
        # Bestimme Command
        if cmd_key == 'custom':
            cmd = data.get('custom_cmd', '')
        else:
            cmd = COMMANDS.get(cmd_key, '')
        
        if not cmd:
            await message.reply_text("❌ Unknown command", reply_markup=get_main_menu_keyboard())
            return
        
        # Feedback an User
        logger.info(f"⚙️  Executing command '{cmd_key}' from User ID: {user_id} (@{username})")
        logger.debug(f"Command: {cmd[:100]}...")
        await message.reply_text(f"⚙️ Running: `{cmd}`", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        
        # Command asynchron ausführen (blockiert Event Loop nicht)
        logger.info(f"🔄 Executing command asynchronously: {cmd_key}")
        result = await run_command_async(cmd, cmd_key, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        # Output zusammenstellen
        output = result.stdout if result.stdout else result.stderr
        if not output and cmd_key == 'bot_logs':
            output = "📋 No log entries yet. Bot is running."
        
        # Spezielle Behandlung für disk_space: JSON für WebApp, Text für Telegram
        if cmd_key == 'disk_space' and output:
            try:
                disks = parse_disk_space(output)
                # Sende JSON-Daten für WebApp (wird in der App gerendert)
                json_data = json.dumps({'type': 'disk_space', 'disks': disks}, indent=2)
                
                # Sende sowohl JSON (für App) als auch Text (für Telegram Chat)
                # Erstelle einen Link zur Mini App mit den Daten als URL-Parameter
                encoded_data = quote(json_data)
                webapp_url_with_data = f"{WEBAPP_URL}?data={encoded_data}"
                
                # Sende JSON + Link zur Visualisierung
                await message.reply_text(
                    f"💾 **Disk Space**\n\n"
                    f"📊 [Visualisierung in der App öffnen]({webapp_url_with_data})\n\n"
                    f"```json\n{json_data}\n```",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"✅ Disk space data sent as JSON ({len(disks)} disks) with visualization link")
                return
            except Exception as e:
                logger.error(f"❌ Error parsing disk space: {e}", exc_info=True)
                # Fallback zu normalem Text-Output
                pass
        
        output = output[:4000] if output else "✅ Done (no output)"
        
        # Ergebnis senden
        output_length = len(output) if output else 0
        logger.info(f"✅ Command '{cmd_key}' completed successfully (output: {output_length} chars)")
        if output_length > 0:
            logger.debug(f"Command output preview: {output[:200]}...")
        await message.reply_text(
            f"```\n{output}\n```", 
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard()
        )
        
    except subprocess.TimeoutExpired:
        logger.warning(f"⏱️  Command '{cmd_key}' timed out after 30s from User ID: {user_id} (@{username})")
        await update.message.reply_text("❌ Timeout (>30s)", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Command '{cmd_key}' execution error from User ID: {user_id} (@{username}): {error_msg}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {error_msg}", reply_markup=get_main_menu_keyboard())

# Thread Pool für subprocess Commands (damit Event Loop nicht blockiert wird)
executor = ThreadPoolExecutor(max_workers=2)

async def run_command_async(cmd, cmd_key, cwd=None):
    """Führt einen Command asynchron aus, ohne Event Loop zu blockieren"""
    logger = logging.getLogger(__name__)
    loop = asyncio.get_event_loop()
    
    def run_subprocess():
        try:
            if cmd_key == 'bot_logs':
                if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
                    log_paths = ['/app/bot/bot.log', 'bot.log', '/app/logs/bot.log']
                    output = None
                    for log_path in log_paths:
                        if os.path.exists(log_path):
                            try:
                                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines = f.readlines()
                                    output = ''.join(lines[-20:]) if len(lines) > 20 else ''.join(lines)
                                    break
                            except:
                                continue
                    if not output:
                        output = '📋 Bot is running in Docker.\n\nTo view logs, use:\n  docker-compose logs -f bot'
                    return FakeResult(output)
                elif IS_WINDOWS:
                    return subprocess.run(
                        ['powershell', '-Command', cmd],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=cwd or os.path.dirname(os.path.abspath(__file__))
                    )
                else:
                    return subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=cwd or os.path.dirname(os.path.abspath(__file__))
                    )
            else:
                if IS_WINDOWS:
                    return subprocess.run(
                        ['powershell', '-Command', cmd],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=cwd or os.path.dirname(os.path.abspath(__file__))
                    )
                else:
                    return subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=cwd or os.path.dirname(os.path.abspath(__file__))
                    )
        except subprocess.TimeoutExpired as e:
            logger.warning(f"⏱️  Command timed out: {cmd[:50]}...")
            raise
        except Exception as e:
            logger.error(f"❌ Command execution error: {e}", exc_info=True)
            raise
    
    # Führe subprocess in Thread Pool aus
    try:
        result = await loop.run_in_executor(executor, run_subprocess)
        return result
    except subprocess.TimeoutExpired:
        raise
    except Exception as e:
        raise

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
    
    # Callback Handler für Quick Actions
    async def handle_quick_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für Quick Action Buttons"""
        logger = logging.getLogger(__name__)
        query = update.callback_query
        
        if not query:
            logger.error("❌ No callback query in update")
            return
        
        logger.info(f"🔔 Callback query received: {query.data}")
        await query.answer()
        
        user_id = query.from_user.id
        username = query.from_user.username or "N/A"
        
        # Finde Index des Users
        try:
            user_index = ALLOWED_USER_IDS.index(user_id)
            match_status = f"Match: User[{user_index}]"
        except ValueError:
            match_status = "No Match"
        
        if user_id not in ALLOWED_USER_IDS:
            logger.warning(f"⚠️  Unauthorized quick action from User ID: {user_id} (@{username}) - {match_status}")
            await query.edit_message_text("❌ Unauthorized", reply_markup=get_inline_menu_keyboard())
            return
        
        action = query.data
        logger.info(f"⚡ Quick action '{action}' from User ID: {user_id} (@{username}) - {match_status}")
        
        # Mappe Quick Actions zu Commands
        action_map = {
            'quick_host_info': 'host_info',
            'quick_system_info': 'system_info',
            'quick_disk_space': 'disk_space',
            'quick_uptime': 'uptime',
            'quick_processes': 'processes',
            'quick_temp': 'temp',
            'quick_memory': 'memory',
            'quick_bot_logs': 'bot_logs'
        }
        
        cmd_key = action_map.get(action)
        if not cmd_key:
            await query.edit_message_text("❌ Unknown action", reply_markup=get_inline_menu_keyboard())
            return
        
        cmd = COMMANDS.get(cmd_key, '')
        if not cmd:
            await query.edit_message_text("❌ Command not found", reply_markup=get_inline_menu_keyboard())
            return
        
        # Command ausführen
        try:
            await query.edit_message_text(f"⚙️ Running: `{cmd}`", parse_mode="Markdown", reply_markup=get_inline_menu_keyboard())
            
            # Command asynchron ausführen (blockiert Event Loop nicht)
            logger.info(f"🔄 Executing quick action command asynchronously: {cmd_key}")
            result = await run_command_async(cmd, cmd_key, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "✅ Done (no output)"
            output = output[:4000] if output else "✅ Done (no output)"
            
            output_length = len(output) if output else 0
            logger.info(f"✅ Quick action '{action}' completed successfully (output: {output_length} chars)")
            
            await query.edit_message_text(
                f"```\n{output}\n```", 
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
            
        except subprocess.TimeoutExpired:
            logger.warning(f"⏱️  Quick action '{action}' timed out after 30s from User ID: {user_id} (@{username})")
            await query.edit_message_text("❌ Timeout (>30s)", reply_markup=get_inline_menu_keyboard())
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Quick action '{action}' error from User ID: {user_id} (@{username}): {error_msg}", exc_info=True)
            await query.edit_message_text(f"❌ Error: {error_msg}", reply_markup=get_inline_menu_keyboard())
    
    # Debug: Alle Updates loggen
    async def log_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Loggt alle Updates für Debugging"""
        logger = logging.getLogger(__name__)
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        username = update.effective_user.username if update.effective_user and update.effective_user.username else "N/A"
        
        if update.message:
            text = update.message.text or update.message.caption or "No text"
            logger.info(f"📨 Message received: '{text[:50]}...' from User ID: {user_id} (@{username})")
            # Prüfe ob WebApp Data vorhanden ist
            if hasattr(update.message, 'web_app_data') and update.message.web_app_data:
                logger.info(f"📱 WebApp data detected in message: {update.message.web_app_data.data}")
                logger.info(f"📱 WebApp data type: {type(update.message.web_app_data)}")
            else:
                logger.debug(f"📨 Message has no web_app_data attribute or it's None")
            # Prüfe alle Attribute der Message
            logger.debug(f"📨 Message attributes: {dir(update.message)}")
        if update.callback_query:
            logger.info(f"🔔 Callback query received: '{update.callback_query.data}' from User ID: {user_id} (@{username})")
        if update.edited_message:
            logger.info(f"✏️  Edited message from User ID: {user_id} (@{username})")
    
    # Handlers registrieren
    # WICHTIG: CallbackQueryHandler muss VOR MessageHandler registriert werden!
    from telegram.ext import CallbackQueryHandler
    # Debug Handler zuerst (mit niedrigster Priorität, group=-1)
    application.add_handler(MessageHandler(filters.ALL, log_all_updates), group=-1)
    application.add_handler(CallbackQueryHandler(log_all_updates), group=-1)
    
    # Handler für Text-Nachrichten von ReplyKeyboard Buttons
    async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für Text-Nachrichten von ReplyKeyboard Buttons"""
        logger = logging.getLogger(__name__)
        user_id = update.effective_user.id
        username = update.effective_user.username or "N/A"
        
        # Finde Index des Users
        try:
            user_index = ALLOWED_USER_IDS.index(user_id)
            match_status = f"Match: User[{user_index}]"
        except ValueError:
            match_status = "No Match"
        
        if user_id not in ALLOWED_USER_IDS:
            logger.warning(f"⚠️  Unauthorized text message from User ID: {user_id} (@{username}) - {match_status}")
            return
        
        text = update.message.text
        logger.info(f"📨 Text message received: '{text}' from User ID: {user_id} (@{username}) - {match_status}")
        
        # Mappe Button-Text zu Commands
        text_to_command = {
            '🏠 Host Info': 'host_info',
            '🖥️ System Info': 'system_info',
            '💾 Disk Space': 'disk_space',
            '🔄 Uptime': 'uptime',
            '📈 Top Prozesse': 'processes',
            '🌡️ Temperature': 'temp',
            '🧠 Memory': 'memory',
            '📋 Bot Logs': 'bot_logs'
        }
        
        cmd_key = text_to_command.get(text)
        if not cmd_key:
            # Nicht ein bekannter Button, ignoriere oder zeige Hilfe
            await update.message.reply_text(
                "❌ Unbekannter Befehl. Bitte verwende die Buttons oder öffne das Control Panel.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        cmd = COMMANDS.get(cmd_key, '')
        if not cmd:
            await update.message.reply_text("❌ Command not found", reply_markup=get_main_menu_keyboard())
            return
        
        # Command ausführen (gleiche Logik wie bei Quick Actions)
        try:
            await update.message.reply_text(f"⚙️ Running: `{cmd}`", parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
            
            logger.info(f"🔄 Executing command from text button asynchronously: {cmd_key}")
            result = await run_command_async(cmd, cmd_key, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "✅ Done (no output)"
            output = output[:4000] if output else "✅ Done (no output)"
            
            output_length = len(output) if output else 0
            logger.info(f"✅ Command '{cmd_key}' from text button completed successfully (output: {output_length} chars)")
            
            await update.message.reply_text(
                f"```\n{output}\n```",
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
            
        except subprocess.TimeoutExpired:
            logger.warning(f"⏱️  Command '{cmd_key}' timed out after 30s from User ID: {user_id} (@{username})")
            await update.message.reply_text("❌ Timeout (>30s)", reply_markup=get_main_menu_keyboard())
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Command '{cmd_key}' execution error from User ID: {user_id} (@{username}): {error_msg}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {error_msg}", reply_markup=get_main_menu_keyboard())
    
    # Eigentliche Handler (group=0, default)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_quick_action))  # VOR MessageHandler!
    # Text-Message Handler für ReplyKeyboard Buttons (muss VOR WebApp Handler sein)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    # WebApp Data Handler - muss explizit auf WEB_APP_DATA filtern
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    logger.info("✅ Handlers registered: /start, CallbackQuery, Text Messages, WebApp Data")
    logger.info("✅ Handlers registered: Debug (group=-1), /start, CallbackQuery, WebApp (group=0)")
    
    # Bot Start Info
    logger.info("=" * 60)
    logger.info("🤖 Bot started successfully")
    logger.info(f"📱 WebApp URL: {WEBAPP_URL}")
    logger.info(f"👥 Allowed Users: {ALLOWED_USER_IDS}")
    logger.info(f"🖥️  Platform: {platform.system()} {platform.release()}")
    logger.info(f"🐍 Python Version: {platform.python_version()}")
    logger.info(f"📂 Working Directory: {os.getcwd()}")
    logger.info("=" * 60)
    
    # Shutdown Handler
    async def shutdown_handler_async():
        """Async shutdown handler"""
        logger.info("=" * 60)
        logger.info("🛑 Bot shutdown initiated")
        logger.info(f"📱 WebApp URL: {WEBAPP_URL}")
        logger.info(f"👥 Allowed Users: {ALLOWED_USER_IDS}")
        logger.info(f"🖥️  Platform: {platform.system()} {platform.release()}")
        logger.info("=" * 60)
        if application:
            try:
                await application.stop()
                await application.shutdown()
                logger.info("✅ Application stopped gracefully")
            except Exception as e:
                logger.error(f"❌ Error during shutdown: {e}", exc_info=True)
    
    def shutdown_handler(signum=None, frame=None):
        """Synchronous wrapper for shutdown"""
        if signum:
            signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else f"Signal {signum}"
            logger.info(f"📶 Received signal: {signal_name}")
        
        # Starte async shutdown
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Wenn Loop läuft, erstelle Task
                loop.create_task(shutdown_handler_async())
            else:
                # Wenn Loop nicht läuft, führe aus
                loop.run_until_complete(shutdown_handler_async())
        except RuntimeError:
            # Keine Event Loop vorhanden, erstelle neue
            asyncio.run(shutdown_handler_async())
    
    # Signal Handler registrieren
    import signal
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, shutdown_handler)
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, shutdown_handler)
    
    # Polling starten
    try:
        logger.info("🔄 Starting polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
    except KeyboardInterrupt:
        logger.info("⌨️  Keyboard interrupt received")
        import asyncio
        try:
            asyncio.run(shutdown_handler_async())
        except RuntimeError:
            # Event Loop läuft bereits, verwende create_task
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Kann nicht awaiten, da wir in sync context sind
                # Application wird durch KeyboardInterrupt selbst gestoppt
                pass
    except Exception as e:
        logger.error(f"❌ Fatal error in polling: {e}", exc_info=True)
        import asyncio
        try:
            asyncio.run(shutdown_handler_async())
        except RuntimeError:
            # Event Loop läuft bereits
            pass
    finally:
        logger.info("👋 Bot shutdown complete")

if __name__ == '__main__':
    main()
