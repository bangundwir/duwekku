import logging
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional

from src.database.sqlite_db import SQLiteDB
from src.models.bot_user import BotUser

logger = logging.getLogger(__name__)


@dataclass
class LimitCheckResult:
    """Result of a limit check."""
    allowed: bool
    message: str
    hourly_used: int
    hourly_limit: int
    daily_used: int
    daily_limit: int
    monthly_used: int
    monthly_limit: int
    reset_minutes: int
    subscription_name: str


class QueryLimiter:
    """Service for enforcing query limits."""
    
    def __init__(self, db: SQLiteDB):
        self.db = db
    
    def set_limits(self, user_id: int, hourly_limit: int, daily_limit: int, monthly_limit: int, reset_hours: int = 1) -> bool:
        """Set hourly, daily and monthly query limits for a user."""
        with self.db._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE bot_users 
                SET hourly_query_limit = ?, daily_query_limit = ?, monthly_query_limit = ?, reset_hours = ?
                WHERE user_id = ?
                """,
                (hourly_limit, daily_limit, monthly_limit, reset_hours, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def check_limit(self, user_id: int) -> dict:
        """Check if user has exceeded their query limits."""
        user = self.db.get_bot_user(user_id)
        
        if not user:
            return {
                "allowed": True,
                "message": "",
                "hourly_used": 0,
                "hourly_limit": 5,
                "daily_used": 0,
                "daily_limit": 10,
                "monthly_used": 0,
                "monthly_limit": 300,
                "reset_minutes": 0,
                "subscription_name": "Free",
            }
        
        # Check resets
        self._check_hourly_reset(user)
        self._check_daily_reset(user)
        self._check_monthly_reset(user)
        
        # Refresh user data
        user = self.db.get_bot_user(user_id)
        reset_minutes = user.get_reset_time_remaining()
        
        base_response = {
            "hourly_used": user.hourly_queries_used,
            "hourly_limit": user.hourly_query_limit,
            "daily_used": user.daily_queries_used,
            "daily_limit": user.daily_query_limit,
            "monthly_used": user.monthly_queries_used,
            "monthly_limit": user.monthly_query_limit,
            "reset_minutes": reset_minutes,
            "subscription_name": user.subscription_plan_name or "Free",
        }
        
        # Check hourly limit
        if user.hourly_queries_used >= user.hourly_query_limit:
            return {
                **base_response,
                "allowed": False,
                "message": f"⏰ Batas per jam tercapai ({user.hourly_queries_used}/{user.hourly_query_limit}). Reset dalam {reset_minutes} menit.",
            }
        
        # Check daily limit
        if user.daily_queries_used >= user.daily_query_limit:
            return {
                **base_response,
                "allowed": False,
                "message": f"📅 Batas harian tercapai ({user.daily_queries_used}/{user.daily_query_limit}). Reset besok.",
            }
        
        # Check monthly limit
        if user.monthly_queries_used >= user.monthly_query_limit:
            return {
                **base_response,
                "allowed": False,
                "message": f"📆 Batas bulanan tercapai ({user.monthly_queries_used}/{user.monthly_query_limit}). Reset bulan depan.",
            }
        
        return {**base_response, "allowed": True, "message": ""}
    
    def _check_hourly_reset(self, user: BotUser) -> None:
        """Check if hourly counter needs to be reset."""
        if user.last_hourly_reset:
            next_reset = user.last_hourly_reset + timedelta(hours=user.reset_hours)
            if datetime.now() >= next_reset:
                with self.db._get_connection() as conn:
                    conn.execute(
                        "UPDATE bot_users SET hourly_queries_used = 0, last_hourly_reset = ? WHERE user_id = ?",
                        (datetime.now().isoformat(), user.user_id)
                    )
                    conn.commit()
        else:
            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE bot_users SET last_hourly_reset = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), user.user_id)
                )
                conn.commit()
    
    def _check_daily_reset(self, user: BotUser) -> None:
        """Check if daily counter needs to be reset."""
        if user.last_query_reset:
            if user.last_query_reset.date() < date.today():
                with self.db._get_connection() as conn:
                    conn.execute(
                        "UPDATE bot_users SET daily_queries_used = 0, last_query_reset = ? WHERE user_id = ?",
                        (datetime.now().isoformat(), user.user_id)
                    )
                    conn.commit()
        else:
            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE bot_users SET last_query_reset = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), user.user_id)
                )
                conn.commit()
    
    def _check_monthly_reset(self, user: BotUser) -> None:
        """Check if monthly counter needs to be reset."""
        if user.last_monthly_reset:
            if (user.last_monthly_reset.year < date.today().year or 
                user.last_monthly_reset.month < date.today().month):
                with self.db._get_connection() as conn:
                    conn.execute(
                        "UPDATE bot_users SET monthly_queries_used = 0, last_monthly_reset = ? WHERE user_id = ?",
                        (datetime.now().isoformat(), user.user_id)
                    )
                    conn.commit()
        else:
            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE bot_users SET last_monthly_reset = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), user.user_id)
                )
                conn.commit()
    
    def increment_usage(self, user_id: int) -> None:
        """Increment user's query counters."""
        with self.db._get_connection() as conn:
            conn.execute(
                """
                UPDATE bot_users 
                SET hourly_queries_used = hourly_queries_used + 1,
                    daily_queries_used = daily_queries_used + 1,
                    monthly_queries_used = monthly_queries_used + 1,
                    total_queries = total_queries + 1
                WHERE user_id = ?
                """,
                (user_id,)
            )
            conn.commit()
    
    def get_usage(self, user_id: int) -> dict:
        """Get user's current usage statistics."""
        user = self.db.get_bot_user(user_id)
        
        if not user:
            return {
                "hourly_used": 0, "hourly_limit": 5, "hourly_remaining": 5,
                "daily_used": 0, "daily_limit": 10, "daily_remaining": 10,
                "monthly_used": 0, "monthly_limit": 300, "monthly_remaining": 300,
                "total_queries": 0, "reset_minutes": 0, "subscription_name": "Free",
            }
        
        return {
            "hourly_used": user.hourly_queries_used,
            "hourly_limit": user.hourly_query_limit,
            "hourly_remaining": user.hourly_queries_remaining,
            "daily_used": user.daily_queries_used,
            "daily_limit": user.daily_query_limit,
            "daily_remaining": user.daily_queries_remaining,
            "monthly_used": user.monthly_queries_used,
            "monthly_limit": user.monthly_query_limit,
            "monthly_remaining": user.monthly_queries_remaining,
            "total_queries": user.total_queries,
            "reset_minutes": user.get_reset_time_remaining(),
            "subscription_name": user.subscription_plan_name or "Free",
        }
