from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class UserSubscription:
    """Model representing a user's subscription assignment."""
    
    user_id: int
    plan_id: int
    plan_name: str
    start_date: date
    end_date: date
    id: Optional[int] = None
    status: str = "active"                          # "active", "expired", "cancelled"
    assigned_by: str = "system"                     # Admin who assigned
    assigned_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
            "start_date": self.start_date.isoformat() if isinstance(self.start_date, date) else self.start_date,
            "end_date": self.end_date.isoformat() if isinstance(self.end_date, date) else self.end_date,
            "status": self.status,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at.isoformat() if isinstance(self.assigned_at, datetime) else self.assigned_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserSubscription":
        """Create UserSubscription from database row dictionary."""
        start_date = data.get("start_date")
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        
        end_date = data.get("end_date")
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        assigned_at = data.get("assigned_at")
        if isinstance(assigned_at, str):
            assigned_at = datetime.fromisoformat(assigned_at)
        elif assigned_at is None:
            assigned_at = datetime.now()
        
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            plan_id=data["plan_id"],
            plan_name=data.get("plan_name", "Unknown"),
            start_date=start_date,
            end_date=end_date,
            status=data.get("status", "active"),
            assigned_by=data.get("assigned_by", "system"),
            assigned_at=assigned_at,
        )
    
    @property
    def days_remaining(self) -> int:
        """Calculate days until expiration."""
        if self.status != "active":
            return 0
        delta = self.end_date - date.today()
        return max(0, delta.days)
    
    @property
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        return self.end_date < date.today() or self.status == "expired"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status == "active" and not self.is_expired
