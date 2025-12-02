from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BotUser:
    """Model representing a bot user for admin dashboard."""
    
    user_id: int                                    # Telegram user ID
    username: Optional[str] = None                  # Telegram username
    first_name: Optional[str] = None                # User's first name
    registered_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    is_blocked: bool = False
    subscription_plan_id: Optional[int] = None      # Current subscription plan
    subscription_plan_name: Optional[str] = None    # Current subscription plan name
    hourly_query_limit: int = 5                     # Hourly query limit
    daily_query_limit: int = 10                     # Daily query limit
    monthly_query_limit: int = 300                  # Monthly query limit
    hourly_queries_used: int = 0                    # This hour's query count
    daily_queries_used: int = 0                     # Today's query count
    monthly_queries_used: int = 0                   # This month's query count
    total_queries: int = 0                          # All-time query count
    last_hourly_reset: Optional[datetime] = None    # Last hourly reset timestamp
    last_query_reset: Optional[datetime] = None     # Last daily reset timestamp
    last_monthly_reset: Optional[datetime] = None   # Last monthly reset timestamp
    reset_hours: int = 1                            # Hours until query reset (configurable)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "registered_at": self.registered_at.isoformat() if isinstance(self.registered_at, datetime) else self.registered_at,
            "last_active": self.last_active.isoformat() if isinstance(self.last_active, datetime) else self.last_active,
            "is_blocked": self.is_blocked,
            "subscription_plan_id": self.subscription_plan_id,
            "subscription_plan_name": self.subscription_plan_name,
            "hourly_query_limit": self.hourly_query_limit,
            "daily_query_limit": self.daily_query_limit,
            "monthly_query_limit": self.monthly_query_limit,
            "hourly_queries_used": self.hourly_queries_used,
            "daily_queries_used": self.daily_queries_used,
            "monthly_queries_used": self.monthly_queries_used,
            "total_queries": self.total_queries,
            "last_hourly_reset": self.last_hourly_reset.isoformat() if self.last_hourly_reset else None,
            "last_query_reset": self.last_query_reset.isoformat() if self.last_query_reset else None,
            "last_monthly_reset": self.last_monthly_reset.isoformat() if self.last_monthly_reset else None,
            "reset_hours": self.reset_hours,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BotUser":
        """Create BotUser from database row dictionary."""
        registered_at = data.get("registered_at")
        if isinstance(registered_at, str):
            registered_at = datetime.fromisoformat(registered_at)
        elif registered_at is None:
            registered_at = datetime.now()
        
        last_active = data.get("last_active")
        if isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active)
        elif last_active is None:
            last_active = datetime.now()
        
        last_query_reset = data.get("last_query_reset")
        if isinstance(last_query_reset, str):
            last_query_reset = datetime.fromisoformat(last_query_reset)
        
        last_monthly_reset = data.get("last_monthly_reset")
        if isinstance(last_monthly_reset, str):
            last_monthly_reset = datetime.fromisoformat(last_monthly_reset)
        
        last_hourly_reset = data.get("last_hourly_reset")
        if isinstance(last_hourly_reset, str):
            last_hourly_reset = datetime.fromisoformat(last_hourly_reset)
        
        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            registered_at=registered_at,
            last_active=last_active,
            is_blocked=bool(data.get("is_blocked", False)),
            subscription_plan_id=data.get("subscription_plan_id"),
            subscription_plan_name=data.get("subscription_plan_name"),
            hourly_query_limit=data.get("hourly_query_limit", 5),
            daily_query_limit=data.get("daily_query_limit", 10),
            monthly_query_limit=data.get("monthly_query_limit", 300),
            hourly_queries_used=data.get("hourly_queries_used", 0),
            daily_queries_used=data.get("daily_queries_used", 0),
            monthly_queries_used=data.get("monthly_queries_used", 0),
            total_queries=data.get("total_queries", 0),
            last_hourly_reset=last_hourly_reset,
            last_query_reset=last_query_reset,
            last_monthly_reset=last_monthly_reset,
            reset_hours=data.get("reset_hours", 1),
        )
    
    @property
    def display_name(self) -> str:
        """Get display name (username or first_name or user_id)."""
        if self.username:
            return f"@{self.username}"
        if self.first_name:
            return self.first_name
        return str(self.user_id)
    
    @property
    def hourly_queries_remaining(self) -> int:
        """Get remaining hourly queries."""
        return max(0, self.hourly_query_limit - self.hourly_queries_used)
    
    @property
    def daily_queries_remaining(self) -> int:
        """Get remaining daily queries."""
        return max(0, self.daily_query_limit - self.daily_queries_used)
    
    @property
    def monthly_queries_remaining(self) -> int:
        """Get remaining monthly queries."""
        return max(0, self.monthly_query_limit - self.monthly_queries_used)
    
    @property
    def is_hourly_limit_reached(self) -> bool:
        """Check if hourly limit is reached."""
        return self.hourly_queries_used >= self.hourly_query_limit
    
    @property
    def is_daily_limit_reached(self) -> bool:
        """Check if daily limit is reached."""
        return self.daily_queries_used >= self.daily_query_limit
    
    @property
    def is_monthly_limit_reached(self) -> bool:
        """Check if monthly limit is reached."""
        return self.monthly_queries_used >= self.monthly_query_limit
    
    def get_reset_time_remaining(self) -> int:
        """Get minutes until hourly reset."""
        if not self.last_hourly_reset:
            return 0
        from datetime import timedelta
        next_reset = self.last_hourly_reset + timedelta(hours=self.reset_hours)
        remaining = (next_reset - datetime.now()).total_seconds() / 60
        return max(0, int(remaining))
