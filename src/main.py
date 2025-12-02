import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings
from src.ai.parser import AIParser
from src.database.sqlite_db import SQLiteDB
from src.database.tidb_db import TiDBCloud
from src.database.manager import DatabaseManager
from src.bot.handler import BotHandler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def create_tidb_connection(settings) -> TiDBCloud | None:
    """Create TiDB connection if credentials are available."""
    if not settings.tidb_user or not settings.tidb_password:
        logger.warning("TiDB credentials not configured, running in SQLite-only mode")
        return None
    
    try:
        tidb = TiDBCloud(
            host=settings.tidb_host,
            port=settings.tidb_port,
            user=settings.tidb_user,
            password=settings.tidb_password,
            database=settings.tidb_database,
            ssl_ca=settings.tidb_ssl_ca,
        )
        
        if tidb.test_connection():
            logger.info("TiDB Cloud connection established")
            return tidb
        else:
            logger.warning("TiDB Cloud connection failed, running in SQLite-only mode")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to connect to TiDB Cloud: {e}")
        return None


def main():
    """Main entry point."""
    logger.info("Starting Money Tracker Bot...")
    
    # Load settings
    settings = get_settings()
    
    # Initialize SQLite database
    sqlite_db = SQLiteDB(settings.sqlite_path)
    logger.info(f"SQLite database initialized at {settings.sqlite_path}")

    
    # Initialize TiDB Cloud (optional)
    tidb_db = create_tidb_connection(settings)
    
    # Initialize database manager
    db_manager = DatabaseManager(sqlite_db, tidb_db)
    
    # Sync pending transactions on startup
    if tidb_db:
        synced = db_manager.sync_pending()
        if synced > 0:
            logger.info(f"Synced {synced} pending transactions to TiDB Cloud")
    
    # Initialize AI parser
    ai_parser = AIParser(
        api_key=settings.poe_api_key,
        base_url=settings.poe_base_url,
        model=settings.poe_model,
    )
    logger.info("AI Parser initialized")
    
    # Initialize and run bot
    bot = BotHandler(
        token=settings.telegram_bot_token,
        ai_parser=ai_parser,
        db_manager=db_manager,
    )
    
    logger.info("Bot is ready! Starting polling...")
    bot.run()


if __name__ == "__main__":
    main()
