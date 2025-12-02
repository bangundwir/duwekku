"""AI Provider Manager - manages multiple AI providers and user preferences."""

import logging
from typing import Optional

from config.settings import Settings
from src.database.sqlite_db import SQLiteDB
from src.ai.providers.base import AIProvider, AIModel, ProviderInfo, ParsedTransaction
from src.ai.providers.poe import PoeProvider
from src.ai.providers.groq import GroqProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages AI providers and user preferences."""
    
    def __init__(self, settings: Settings, sqlite_db: SQLiteDB):
        self.settings = settings
        self.sqlite_db = sqlite_db
        self.providers: dict[str, AIProvider] = {}
        self._init_providers()
    
    def _init_providers(self) -> None:
        """Initialize all configured providers."""
        # Initialize Poe provider if configured
        if self.settings.poe_api_key:
            try:
                self.providers["poe"] = PoeProvider(
                    api_key=self.settings.poe_api_key,
                    base_url=self.settings.poe_base_url,
                    model=self.settings.poe_model
                )
                logger.info("Poe provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Poe provider: {e}")
        
        # Initialize Groq provider if configured
        if self.settings.groq_api_key:
            try:
                self.providers["groq"] = GroqProvider(
                    api_key=self.settings.groq_api_key,
                    base_url=self.settings.groq_base_url,
                    model=self.settings.groq_model
                )
                logger.info("Groq provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Groq provider: {e}")
    
    def _get_default_provider(self) -> Optional[AIProvider]:
        """Get the default provider based on settings."""
        default = self.settings.default_ai_provider
        if default in self.providers:
            return self.providers[default]
        # Fallback to first available provider
        if self.providers:
            return next(iter(self.providers.values()))
        return None
    
    def get_provider(self, user_id: int) -> Optional[AIProvider]:
        """Get the active provider for a user."""
        # Check user preference
        pref = self.sqlite_db.get_user_preference(user_id)
        
        if pref and pref.provider in self.providers:
            provider = self.providers[pref.provider]
            # Set user's preferred model if specified
            if pref.model:
                provider.set_model(pref.model)
            return provider
        
        return self._get_default_provider()
    
    def set_user_provider(self, user_id: int, provider_name: str) -> bool:
        """Set user's preferred provider."""
        if provider_name not in self.providers:
            return False
        
        # Get current preference to preserve model if same provider
        current_pref = self.sqlite_db.get_user_preference(user_id)
        model = None
        if current_pref and current_pref.provider == provider_name:
            model = current_pref.model
        
        return self.sqlite_db.save_user_preference(user_id, provider_name, model)
    
    def set_user_model(self, user_id: int, model_id: str) -> bool:
        """Set user's preferred model."""
        # Get current preference or use default provider
        pref = self.sqlite_db.get_user_preference(user_id)
        provider_name = pref.provider if pref else self.settings.default_ai_provider
        
        if provider_name not in self.providers:
            return False
        
        return self.sqlite_db.save_user_preference(user_id, provider_name, model_id)
    
    def list_providers(self) -> list[ProviderInfo]:
        """List all available providers with status."""
        all_providers = [
            ("poe", "Poe (Quora)", bool(self.settings.poe_api_key)),
            ("groq", "Groq", bool(self.settings.groq_api_key)),
        ]
        
        result = []
        for name, display_name, is_configured in all_providers:
            current_model = None
            if name in self.providers:
                current_model = self.providers[name].get_current_model()
            
            result.append(ProviderInfo(
                name=name,
                display_name=display_name,
                is_configured=is_configured,
                current_model=current_model
            ))
        
        return result
    
    def list_models(self, user_id: int) -> list[AIModel]:
        """List models for user's current provider."""
        provider = self.get_provider(user_id)
        if provider:
            return provider.list_models()
        return []
    
    def parse_transaction(self, user_id: int, message: str) -> Optional[ParsedTransaction]:
        """Parse transaction using user's preferred provider."""
        provider = self.get_provider(user_id)
        if provider:
            return provider.parse_transaction(message)
        return None
    
    def get_user_provider_info(self, user_id: int) -> Optional[ProviderInfo]:
        """Get info about user's current provider."""
        provider = self.get_provider(user_id)
        if provider:
            return provider.get_info()
        return None
    
    def test_provider(self, provider_name: str) -> bool:
        """Test if a specific provider is working."""
        if provider_name in self.providers:
            return self.providers[provider_name].test_connection()
        return False
