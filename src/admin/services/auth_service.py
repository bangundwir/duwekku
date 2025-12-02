import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from src.database.sqlite_db import SQLiteDB
from src.models.admin_session import AdminSession, generate_session_token

logger = logging.getLogger(__name__)


class AuthService:
    """Service for admin authentication."""
    
    def __init__(self, db: SQLiteDB, admin_username: str, admin_password: str):
        self.db = db
        self.admin_username = admin_username
        self.admin_password_hash = self._hash_password(admin_password)
        self.session_timeout_minutes = 30
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return self._hash_password(password) == self.admin_password_hash
    
    def login(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate admin and create session.
        Returns session token if successful, None otherwise.
        """
        if username != self.admin_username:
            logger.warning(f"Login failed: invalid username '{username}'")
            return None
        
        if not self._verify_password(password):
            logger.warning(f"Login failed: invalid password for '{username}'")
            return None
        
        # Create new session
        session = AdminSession(
            admin_username=username,
            token=generate_session_token(),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=self.session_timeout_minutes),
        )
        
        self.db.create_admin_session(session)
        logger.info(f"Admin '{username}' logged in successfully")
        
        return session.token
    
    def logout(self, token: str) -> bool:
        """Invalidate a session. Returns True if successful."""
        result = self.db.invalidate_admin_session(token)
        if result:
            logger.info(f"Session invalidated: {token[:8]}...")
        return result
    
    def validate_session(self, token: str) -> Optional[AdminSession]:
        """
        Validate a session token.
        Returns AdminSession if valid, None otherwise.
        """
        if not token:
            return None
        
        session = self.db.get_admin_session(token)
        
        if not session:
            return None
        
        if not session.is_active:
            return None
        
        # Refresh session expiration on activity
        new_expires = datetime.now() + timedelta(minutes=self.session_timeout_minutes)
        self.db.refresh_admin_session(token, new_expires)
        
        return session
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns count of removed."""
        count = self.db.cleanup_expired_sessions()
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
        return count
