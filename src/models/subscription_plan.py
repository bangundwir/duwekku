from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json


@dataclass
class SubscriptionPlan:
    """Model representing a subscription plan for bot users."""
    
    name: str                                       # e.g., "Basic", "Premium", "Pro"
    daily_query_limit: int                          # Queries per day
    monthly_query_limit: int                        # Queries per month
    price: float                                    # Price in IDR
    duration_days: int                              # Plan duration in days
    id: Optional[int] = None
    features: List[str] = field(default_factory=list)  # List of features
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "name": self.name,
            "daily_query_limit": self.daily_query_limit,
            "monthly_query_limit": self.monthly_query_limit,
            "price": self.price,
            "duration_days": self.duration_days,
            "features": json.dumps(self.features) if self.features else "[]",
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SubscriptionPlan":
        """Create SubscriptionPlan from database row dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        features = data.get("features", "[]")
        if isinstance(features, str):
            try:
                features = json.loads(features)
            except json.JSONDecodeError:
                features = []
        
        return cls(
            id=data.get("id"),
            name=data["name"],
            daily_query_limit=data.get("daily_query_limit", 10),
            monthly_query_limit=data.get("monthly_query_limit", 300),
            price=float(data.get("price", 0)),
            duration_days=data.get("duration_days", 30),
            features=features if isinstance(features, list) else [],
            is_active=bool(data.get("is_active", True)),
            created_at=created_at,
        )
    
    def format_price(self) -> str:
        """Format price with thousand separator."""
        return f"Rp {self.price:,.0f}".replace(",", ".")
    
    def format_duration(self) -> str:
        """Format duration in human readable form."""
        if self.duration_days == 30:
            return "1 bulan"
        elif self.duration_days == 365:
            return "1 tahun"
        elif self.duration_days % 30 == 0:
            months = self.duration_days // 30
            return f"{months} bulan"
        else:
            return f"{self.duration_days} hari"


# Default plans
DEFAULT_PLANS = [
    SubscriptionPlan(
        name="Free",
        daily_query_limit=10,
        monthly_query_limit=100,
        price=0,
        duration_days=0,  # Unlimited
        features=["10 query/hari", "100 query/bulan", "Fitur dasar"],
    ),
    SubscriptionPlan(
        name="Basic",
        daily_query_limit=50,
        monthly_query_limit=500,
        price=25000,
        duration_days=30,
        features=["50 query/hari", "500 query/bulan", "Export CSV", "Analisis dasar"],
    ),
    SubscriptionPlan(
        name="Premium",
        daily_query_limit=200,
        monthly_query_limit=2000,
        price=75000,
        duration_days=30,
        features=["200 query/hari", "2000 query/bulan", "Export CSV/Excel", "Analisis lengkap", "Priority support"],
    ),
    SubscriptionPlan(
        name="Pro",
        daily_query_limit=1000,
        monthly_query_limit=10000,
        price=150000,
        duration_days=30,
        features=["1000 query/hari", "10000 query/bulan", "Semua fitur", "API access", "Priority support"],
    ),
]
