import os
import json
import subprocess
import sys
import platform
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_IDS = json.loads(os.getenv("ALLOWED_USER_IDS", "[]"))
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

# Predefined Commands (platform-specific)
if IS_WINDOWS:
    COMMANDS = {
        'system_info': 'systeminfo',
        'disk_space': 'wmic logicaldisk get size,freespace,caption',
        'uptime': 'net stats srv',
        'processes': 'tasklist /FO TABLE /SORT:CPU',
        'temp': 'wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature',
        'memory': 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list'
    }
else:
    COMMANDS = {
        'system_info': 'neofetch',
        'disk_space': 'df -h',
        'uptime': 'uptime',
        'processes': 'ps aux --sort=-%cpu | head -15',
        'temp': 'sensors',
        'memory': 'free -h'
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für /start Command"""
    user_id = update.effective_user.id
    
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("❌ Unauthorized")
        print(f"⚠️  Unauthorized access attempt: {user_id}", file=sys.stderr)
        return
    
    keyboard = [
        [InlineKeyboardButton("🚀 Open Control Panel", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Bot aktiv!\nUser ID: {user_id}\n\nÖffne das Control Panel:",
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler für WebApp Data (Commands von Mini App)"""
    if update.effective_user.id not in ALLOWED_USER_IDS:
        return
    
    try:
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
        await update.message.reply_text(f"⚙️ Running: `{cmd}`", parse_mode="Markdown")
        
        # Command ausführen
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Output zusammenstellen
        output = result.stdout if result.stdout else result.stderr
        output = output[:4000] if output else "✅ Done (no output)"
        
        # Ergebnis senden
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")
        
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout (>30s)")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        print(f"Error: {e}", file=sys.stderr)

def main():
    """Main Function"""
    # Validierung
    if not TOKEN:
        print("❌ BOT_TOKEN not set!", file=sys.stderr)
        sys.exit(1)
    if not ALLOWED_USER_IDS:
        print("❌ ALLOWED_USER_IDS not set!", file=sys.stderr)
        sys.exit(1)
    if not WEBAPP_URL:
        print("❌ WEBAPP_URL not set!", file=sys.stderr)
        sys.exit(1)
    
    # Application erstellen
    application = Application.builder().token(TOKEN).build()
    
    # Handlers registrieren
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Info ausgeben
    import sys
    import io
    # UTF-8 Encoding für Windows Console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print(f"🤖 Bot started successfully")
    print(f"📱 WebApp URL: {WEBAPP_URL}")
    print(f"👥 Allowed Users: {ALLOWED_USER_IDS}")
    
    # Polling starten
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
