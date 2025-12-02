import logging
from dataclasses import dataclass
from typing import Optional, List

from src.database.sqlite_db import SQLiteDB
from src.models.bot_user import BotUser

logger = logging.getLogger(__name__)


@dataclass
class PaginatedResult:
    """Paginated result container."""
    items: List[BotUser]
    total: int
    page: int
    per_page: int
    total_pages: int


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: SQLiteDB):
        self.db = db
    
    def get_users(
        self, 
        page: int = 1, 
        per_page: int = 20, 
        search: Optional[str] = None
    ) -> PaginatedResult:
        """Get paginated list of users with optional search."""
        users, total = self.db.get_all_bot_users(page, per_page, search)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return PaginatedResult(
            items=users,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )
    
    def get_user(self, user_id: int) -> Optional[BotUser]:
        """Get a single user by ID."""
        return self.db.get_bot_user(user_id)
    
    def register_user(
        self, 
        user_id: int, 
        username: Optional[str] = None, 
        first_name: Optional[str] = None
    ) -> BotUser:
        """Register or update a user."""
        return self.db.register_bot_user(user_id, username, first_name)
    
    def update_activity(self, user_id: int) -> None:
        """Update user's last active timestamp."""
        self.db.update_bot_user_activity(user_id)
    
    def block_user(self, user_id: int) -> Optional[BotUser]:
        """Block a user. Returns updated user or None if not found."""
        if self.db.block_bot_user(user_id):
            return self.db.get_bot_user(user_id)
        return None
    
    def unblock_user(self, user_id: int) -> Optional[BotUser]:
        """Unblock a user. Returns updated user or None if not found."""
        if self.db.unblock_bot_user(user_id):
            return self.db.get_bot_user(user_id)
        return None
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all related data."""
        return self.db.delete_bot_user(user_id)
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Check if a user is blocked."""
        user = self.db.get_bot_user(user_id)
        return user.is_blocked if user else False
    
    def get_user_stats(self) -> dict:
        """Get user statistics."""
        return self.db.get_bot_user_stats()
    
    def set_user_limits(self, user_id: int, daily_limit: int, monthly_limit: int) -> bool:
        """Set user's query limits."""
        return self.db.update_bot_user_limits(user_id, daily_limit, monthly_limit)
