from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram
    telegram_bot_token: str
    
    # Poe API
    poe_api_key: str = ""
    poe_base_url: str = "https://api.poe.com/v1"
    poe_model: str = "gemini-2.5-flash"
    
    # Groq API
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Default AI Provider
    default_ai_provider: str = "groq"
    
    # TiDB Cloud
    tidb_host: str = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
    tidb_port: int = 4000
    tidb_user: str = ""
    tidb_password: str = ""
    tidb_database: str = "test"
    tidb_ssl_ca: str = "isrgrootx1.pem"
    
    # SQLite
    sqlite_path: str = "data/money_tracker.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
