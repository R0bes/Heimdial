#!/usr/bin/env python3
"""
Development Server mit Hot Reload
Startet den Bot neu, wenn sich Code-Dateien ändern
"""
import os
import sys
import subprocess
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class BotReloadHandler(FileSystemEventHandler):
    """Handler für File-Änderungen"""
    def __init__(self, bot_process):
        self.bot_process = bot_process
        self.last_reload = 0
        self.reload_delay = 2  # Mindest-Abstand zwischen Reloads (Sekunden)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Nur Python-Dateien beobachten
        if not event.src_path.endswith('.py'):
            return
        
        # Ignoriere __pycache__ und .pyc Dateien
        if '__pycache__' in event.src_path or event.src_path.endswith('.pyc'):
            return
        
        current_time = time.time()
        if current_time - self.last_reload < self.reload_delay:
            return
        
        self.last_reload = current_time
        logger.info(f"🔄 File changed: {event.src_path}")
        logger.info("🔄 Reloading bot...")
        
        # Bot-Prozess beenden
        if self.bot_process and self.bot_process.poll() is None:
            logger.info("🛑 Stopping bot process...")
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Force killing bot process...")
                self.bot_process.kill()
        
        # Bot neu starten
        logger.info("🚀 Starting bot process...")
        self.bot_process = subprocess.Popen(
            [sys.executable, 'bot.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        logger.info(f"✅ Bot restarted (PID: {self.bot_process.pid})")

def main():
    """Main Function für Development Server"""
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    bot_script = os.path.join(bot_dir, 'bot.py')
    
    if not os.path.exists(bot_script):
        logger.error(f"❌ Bot script not found: {bot_script}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("🔥 Development Server mit Hot Reload")
    logger.info(f"📂 Watching: {bot_dir}")
    logger.info("=" * 60)
    
    # Bot initial starten
    logger.info("🚀 Starting bot...")
    bot_process = subprocess.Popen(
        [sys.executable, 'bot.py'],
        cwd=bot_dir,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    logger.info(f"✅ Bot started (PID: {bot_process.pid})")
    
    # File Watcher einrichten
    event_handler = BotReloadHandler(bot_process)
    observer = Observer()
    observer.schedule(event_handler, bot_dir, recursive=False)
    observer.start()
    
    logger.info("👀 Watching for file changes...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            # Prüfe ob Bot-Prozess noch läuft
            if bot_process.poll() is not None:
                logger.error("❌ Bot process died, restarting...")
                bot_process = subprocess.Popen(
                    [sys.executable, 'bot.py'],
                    cwd=bot_dir,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
                event_handler.bot_process = bot_process
                logger.info(f"✅ Bot restarted (PID: {bot_process.pid})")
            
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⌨️  Keyboard interrupt received")
        observer.stop()
        if bot_process.poll() is None:
            logger.info("🛑 Stopping bot process...")
            bot_process.terminate()
            try:
                bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                bot_process.kill()
    
    observer.join()
    logger.info("👋 Development server stopped")

if __name__ == '__main__':
    main()

