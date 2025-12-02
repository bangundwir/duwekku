"""User preference model for AI provider settings."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserPreference:
    """Model representing user's AI provider preference."""
    
    user_id: int
    provider: str  # "poe" or "groq"
    model: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert preference to dictionary for database storage."""
        return {
            "user_id": self.user_id,
            "provider": self.provider,
            "model": self.model,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserPreference":
        """Create UserPreference from database row dictionary."""
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()
            
        return cls(
            user_id=data["user_id"],
            provider=data["provider"],
            model=data.get("model"),
            updated_at=updated_at,
        )
    
    def format_display(self) -> str:
        """Format preference for display."""
        model_str = self.model or "default"
        return f"🤖 Provider: {self.provider}\n📦 Model: {model_str}"
