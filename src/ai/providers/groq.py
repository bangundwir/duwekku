"""Groq AI Provider implementation."""

import json
import re
import logging
from typing import Optional

import openai
import httpx

from .base import AIProvider, AIModel, ParsedTransaction, ParsedSubscription

logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """Groq API provider using OpenAI-compatible interface."""
    
    name = "groq"
    display_name = "Groq"
    
    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1", model: str = "llama-3.3-70b-versatile"):
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
                max_tokens=500,
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content, message)
            
        except Exception as e:
            logger.error(f"Groq parsing error: {e}")
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
            logger.error(f"Failed to parse Groq response: {e}")
            return None
    
    def parse_subscription(self, message: str) -> Optional[ParsedSubscription]:
        """Parse natural language message into subscription data."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": self._build_subscription_prompt(message)}
                ],
                temperature=0.1,
                max_tokens=500,
            )
            
            content = response.choices[0].message.content
            return self._parse_subscription_response(content)
            
        except Exception as e:
            logger.error(f"Groq subscription parsing error: {e}")
            return None
    
    def _parse_subscription_response(self, response: str) -> Optional[ParsedSubscription]:
        """Parse AI response JSON into ParsedSubscription."""
        try:
            response = response.strip()
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                response = json_match.group()
            
            data = json.loads(response)
            
            # Normalize category
            category = data.get("category", "other").lower()
            valid_categories = ["streaming", "hosting", "domain", "software", "other"]
            if category not in valid_categories:
                category = "other"
            
            parsed = ParsedSubscription(
                name=data.get("name", ""),
                amount=float(data.get("amount", 0)),
                category=category,
                duration_months=int(data.get("duration_months", 1)),
            )
            
            if parsed.is_valid():
                return parsed
            return None
            
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse subscription response: {e}")
            return None
    
    def list_models(self) -> list[AIModel]:
        """Fetch available models from Groq API."""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                
                data = response.json()
                models = data.get("data", [])
                
                # Sort by id and return
                result = []
                for m in sorted(models, key=lambda x: x.get("id", "")):
                    model_id = m.get("id", "")
                    # Skip deprecated or internal models
                    if model_id and not model_id.startswith("whisper"):
                        result.append(AIModel(
                            id=model_id,
                            name=model_id,
                            description=m.get("owned_by", "")
                        ))
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch Groq models: {e}")
            # Return fallback list
            return [
                AIModel("llama-3.3-70b-versatile", "Llama 3.3 70B Versatile"),
                AIModel("llama-3.1-8b-instant", "Llama 3.1 8B Instant"),
                AIModel("mixtral-8x7b-32768", "Mixtral 8x7B"),
                AIModel("gemma2-9b-it", "Gemma 2 9B"),
            ]
    
    def test_connection(self) -> bool:
        """Test if Groq connection is working."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Groq connection test failed: {e}")
            return False
    
    def set_model(self, model_id: str) -> bool:
        """Set the active model."""
        self.model = model_id
        return True
    
    def get_current_model(self) -> str:
        """Get the current model ID."""
        return self.model
