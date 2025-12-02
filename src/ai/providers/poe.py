"""Poe AI Provider implementation."""

import json
import re
import logging
from typing import Optional

import openai

from .base import AIProvider, AIModel, ParsedTransaction

logger = logging.getLogger(__name__)


class PoeProvider(AIProvider):
    """Poe API provider using OpenAI-compatible interface."""
    
    name = "poe"
    display_name = "Poe (Quora)"
    
    # Predefined models available on Poe
    AVAILABLE_MODELS = [
        AIModel("gemini-2.5-flash", "Gemini 2.5 Flash", "Google's fast Gemini model"),
        AIModel("gpt-4o", "GPT-4o", "OpenAI's GPT-4o model"),
        AIModel("gpt-4o-mini", "GPT-4o Mini", "OpenAI's smaller GPT-4o"),
        AIModel("claude-3.5-sonnet", "Claude 3.5 Sonnet", "Anthropic's Claude model"),
        AIModel("claude-3-haiku", "Claude 3 Haiku", "Anthropic's fast Claude model"),
        AIModel("llama-3.1-405b", "Llama 3.1 405B", "Meta's largest Llama model"),
    ]
    
    def __init__(self, api_key: str, base_url: str = "https://api.poe.com/v1", model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    def parse_transaction(self, message: str) -> Optional[ParsedTransaction]:
        """Parse natural language message into transaction data."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": self._build_prompt(message)}
                ],
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content, message)
            
        except Exception as e:
            logger.error(f"Poe parsing error: {e}")
            return None
    
    def _parse_response(self, response: str, original_message: str) -> Optional[ParsedTransaction]:
        """Parse AI response JSON into ParsedTransaction."""
        try:
            response = response.strip()
            
            # Find JSON in response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                response = json_match.group()
            
            data = json.loads(response)
            
            parsed = ParsedTransaction(
                type=data.get("type", "expense"),
                amount=float(data.get("amount", 0)),
                category=data.get("category", "lainnya"),
                description=data.get("description", original_message),
            )
            
            if parsed.is_valid():
                return parsed
            return None
            
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse Poe response: {e}")
            return None
    
    def list_models(self) -> list[AIModel]:
        """Return predefined list of Poe models."""
        return self.AVAILABLE_MODELS.copy()
    
    def test_connection(self) -> bool:
        """Test if Poe connection is working."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return True
        except Exception as e:
            logger.error(f"Poe connection test failed: {e}")
            return False
    
    def set_model(self, model_id: str) -> bool:
        """Set the active model."""
        valid_ids = [m.id for m in self.AVAILABLE_MODELS]
        if model_id in valid_ids:
            self.model = model_id
            return True
        return False
    
    def get_current_model(self) -> str:
        """Get the current model ID."""
        return self.model
