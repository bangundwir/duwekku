from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import secrets


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


@dataclass
class AdminSession:
    """Model representing an admin session for authentication."""
    
    admin_username: str
    token: str = field(default_factory=generate_session_token)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=30))
    is_valid: bool = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "token": self.token,
            "admin_username": self.admin_username,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "expires_at": self.expires_at.isoformat() if isinstance(self.expires_at, datetime) else self.expires_at,
            "is_valid": self.is_valid,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AdminSession":
        """Create AdminSession from database row dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        expires_at = data.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        elif expires_at is None:
            expires_at = datetime.now() + timedelta(minutes=30)
        
        return cls(
            token=data["token"],
            admin_username=data["admin_username"],
            created_at=created_at,
            expires_at=expires_at,
            is_valid=bool(data.get("is_valid", True)),
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Check if session is still active (valid and not expired)."""
        return self.is_valid and not self.is_expired
    
    def refresh(self, minutes: int = 30) -> None:
        """Extend session expiration time."""
        self.expires_at = datetime.now() + timedelta(minutes=minutes)
    
    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_valid = False
