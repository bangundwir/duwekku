"""
Script untuk menjalankan Bot Telegram dan Admin Dashboard bersamaan.
Jalankan dengan: uv run python run_all.py
"""
import asyncio
import logging
import threading
import signal
import sys

import uvicorn

from config.settings import get_settings
from src.database.sqlite_db import SQLiteDB
from src.database.tidb_db import TiDBCloud
from src.database.manager import DatabaseManager
from src.ai.provider_manager import ProviderManager
from src.bot.handler import BotHandler
from src.admin.api import create_admin_api

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_admin_dashboard(settings):
    """Run admin dashboard in a separate thread with its own database connection."""
    # Create separate database connection for this thread
    admin_db = SQLiteDB(settings.sqlite_path)
    
    app = create_admin_api(
        db=admin_db,
        admin_username=settings.admin_username,
        admin_password=settings.admin_password,
    )
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.admin_port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    server.run()


async def run_bot(settings, db_manager, provider_manager):
    """Run Telegram bot."""
    bot = BotHandler(
        token=settings.telegram_bot_token,
        db_manager=db_manager,
        provider_manager=provider_manager,
    )
    
    app = bot.setup()
    
    logger.info("Starting Telegram Bot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message", "callback_query"])
    
    # Keep running until interrupted
    stop_event = asyncio.Event()
    
    def signal_handler():
        stop_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    await stop_event.wait()
    
    logger.info("Stopping bot...")
    await app.updater.stop()
    await app.stop()
    await app.shutdown()


def main():
    """Main entry point."""
    settings = get_settings()
    
    # Initialize database
    logger.info("Initializing database...")
    sqlite_db = SQLiteDB(settings.sqlite_path)
    
    # Try to connect to TiDB Cloud (optional)
    tidb_db = None
    if settings.tidb_user and settings.tidb_password:
        try:
            tidb_db = TiDBCloud(
                host=settings.tidb_host,
                port=settings.tidb_port,
                user=settings.tidb_user,
                password=settings.tidb_password,
                database=settings.tidb_database,
                ssl_ca=settings.tidb_ssl_ca,
            )
            logger.info("Connected to TiDB Cloud")
        except Exception as e:
            logger.warning(f"Failed to connect to TiDB Cloud: {e}")
    
    db_manager = DatabaseManager(sqlite_db, tidb_db)
    
    # Initialize AI provider manager
    provider_manager = ProviderManager(settings, sqlite_db)
    
    # Start admin dashboard in a separate thread
    logger.info(f"Starting Admin Dashboard on http://localhost:{settings.admin_port}")
    dashboard_thread = threading.Thread(
        target=run_admin_dashboard,
        args=(settings,),
        daemon=True
    )
    dashboard_thread.start()
    
    # Run bot in main thread
    logger.info("Starting Telegram Bot...")
    try:
        asyncio.run(run_bot(settings, db_manager, provider_manager))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        sqlite_db.close()
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
