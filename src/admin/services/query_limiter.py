import logging
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from src.database.sqlite_db import SQLiteDB
from src.models.bot_user import BotUser

logger = logging.getLogger(__name__)


@dataclass
class LimitCheckResult:
    """Result of a limit check."""
    allowed: bool
    message: str
    daily_used: int
    daily_limit: int
    monthly_used: int
    monthly_limit: int


class QueryLimiter:
    """Service for enforcing query limits."""
    
    def __init__(self, db: SQLiteDB):
        self.db = db
    
    def set_limits(self, user_id: int, daily_limit: int, monthly_limit: int) -> bool:
        """Set daily and monthly query limits for a user."""
        return self.db.update_bot_user_limits(user_id, daily_limit, monthly_limit)
    
    def check_limit(self, user_id: int) -> dict:
        """
        Check if user has exceeded their query limits.
        Returns dict with 'allowed' boolean and 'message' string.
        """
        user = self.db.get_bot_user(user_id)
        
        if not user:
            # New user, allow and will be registered
            return {
                "allowed": True,
                "message": "",
                "daily_used": 0,
                "daily_limit": 10,
                "monthly_used": 0,
                "monthly_limit": 300,
            }
        
        # Check if we need to reset daily counter
        self._check_daily_reset(user)
        
        # Check if we need to reset monthly counter
        self._check_monthly_reset(user)
        
        # Refresh user data after potential resets
        user = self.db.get_bot_user(user_id)
        
        # Check daily limit
        if user.daily_queries_used >= user.daily_query_limit:
            return {
                "allowed": False,
                "message": f"Batas harian tercapai ({user.daily_queries_used}/{user.daily_query_limit} query). Reset besok.",
                "daily_used": user.daily_queries_used,
                "daily_limit": user.daily_query_limit,
                "monthly_used": user.monthly_queries_used,
                "monthly_limit": user.monthly_query_limit,
            }
        
        # Check monthly limit
        if user.monthly_queries_used >= user.monthly_query_limit:
            return {
                "allowed": False,
                "message": f"Batas bulanan tercapai ({user.monthly_queries_used}/{user.monthly_query_limit} query). Reset bulan depan.",
                "daily_used": user.daily_queries_used,
                "daily_limit": user.daily_query_limit,
                "monthly_used": user.monthly_queries_used,
                "monthly_limit": user.monthly_query_limit,
            }
        
        return {
            "allowed": True,
            "message": "",
            "daily_used": user.daily_queries_used,
            "daily_limit": user.daily_query_limit,
            "monthly_used": user.monthly_queries_used,
            "monthly_limit": user.monthly_query_limit,
        }
    
    def _check_daily_reset(self, user: BotUser) -> None:
        """Check if daily counter needs to be reset."""
        if user.last_query_reset:
            last_reset_date = user.last_query_reset.date()
            if last_reset_date < date.today():
                # Reset daily counter for this user
                with self.db._get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE bot_users 
                        SET daily_queries_used = 0, last_query_reset = ?
                        WHERE user_id = ?
                        """,
                        (datetime.now().isoformat(), user.user_id)
                    )
                    conn.commit()
        else:
            # First time, set the reset timestamp
            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE bot_users SET last_query_reset = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), user.user_id)
                )
                conn.commit()
    
    def _check_monthly_reset(self, user: BotUser) -> None:
        """Check if monthly counter needs to be reset."""
        if user.last_monthly_reset:
            last_reset_month = user.last_monthly_reset.month
            last_reset_year = user.last_monthly_reset.year
            current_month = date.today().month
            current_year = date.today().year
            
            if (current_year > last_reset_year) or (current_year == last_reset_year and current_month > last_reset_month):
                # Reset monthly counter for this user
                with self.db._get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE bot_users 
                        SET monthly_queries_used = 0, last_monthly_reset = ?
                        WHERE user_id = ?
                        """,
                        (datetime.now().isoformat(), user.user_id)
                    )
                    conn.commit()
        else:
            # First time, set the reset timestamp
            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE bot_users SET last_monthly_reset = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), user.user_id)
                )
                conn.commit()
    
    def increment_usage(self, user_id: int) -> None:
        """Increment user's query counters."""
        self.db.increment_user_query_count(user_id)
    
    def get_usage(self, user_id: int) -> dict:
        """Get user's current usage statistics."""
        user = self.db.get_bot_user(user_id)
        
        if not user:
            return {
                "daily_used": 0,
                "daily_limit": 10,
                "daily_remaining": 10,
                "monthly_used": 0,
                "monthly_limit": 300,
                "monthly_remaining": 300,
                "total_queries": 0,
            }
        
        return {
            "daily_used": user.daily_queries_used,
            "daily_limit": user.daily_query_limit,
            "daily_remaining": user.daily_queries_remaining,
            "monthly_used": user.monthly_queries_used,
            "monthly_limit": user.monthly_query_limit,
            "monthly_remaining": user.monthly_queries_remaining,
            "total_queries": user.total_queries,
        }
    
    def reset_daily_limits(self) -> int:
        """Reset daily query counts for all users. Returns count of users reset."""
        return self.db.reset_daily_query_counts()
    
    def reset_monthly_limits(self) -> int:
        """Reset monthly query counts for all users. Returns count of users reset."""
        return self.db.reset_monthly_query_counts()
