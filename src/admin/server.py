"""Admin Dashboard Server - Run separately from the bot."""
import logging
import uvicorn

from config.settings import get_settings
from src.database.sqlite_db import SQLiteDB
from src.admin.api import create_admin_api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Start the admin dashboard server."""
    settings = get_settings()
    
    # Initialize database
    db = SQLiteDB(settings.sqlite_path)
    
    # Create FastAPI app
    app = create_admin_api(
        db=db,
        admin_username=settings.admin_username,
        admin_password=settings.admin_password,
    )
    
    logger.info(f"Starting Admin Dashboard on http://localhost:{settings.admin_port}")
    logger.info(f"Login with username: {settings.admin_username}")
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.admin_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
