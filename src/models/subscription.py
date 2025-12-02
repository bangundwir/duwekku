from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


SUBSCRIPTION_CATEGORIES = [
    "streaming",    # Netflix, Spotify, YouTube Premium
    "hosting",      # VPS, Cloud services
    "domain",       # Domain names
    "software",     # SaaS, apps
    "other"
]


@dataclass
class Subscription:
    """Model representing a subscription/recurring payment."""
    
    user_id: int
    name: str
    amount: float
    category: str
    start_date: date
    end_date: date
    id: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    synced: bool = False
    
    @property
    def days_remaining(self) -> int:
        """Calculate days until expiration."""
        if not self.is_active:
            return 0
        delta = self.end_date - date.today()
        return max(0, delta.days)
    
    @property
    def status(self) -> str:
        """Return status based on end_date and is_active."""
        if not self.is_active or self.end_date < date.today():
            return "expired"
        elif self.days_remaining <= 7:
            return "expiring_soon"
        return "active"
    
    def to_dict(self) -> dict:
        """Convert subscription to dictionary for database storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": self.amount,
            "category": self.category,
            "start_date": self.start_date.isoformat() if isinstance(self.start_date, date) else self.start_date,
            "end_date": self.end_date.isoformat() if isinstance(self.end_date, date) else self.end_date,
            "is_active": self.is_active,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "synced": self.synced,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Subscription":
        """Create Subscription from database row dictionary."""
        start_date = data.get("start_date")
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        
        end_date = data.get("end_date")
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
            
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            name=data["name"],
            amount=float(data["amount"]),
            category=data.get("category", "other"),
            start_date=start_date,
            end_date=end_date,
            is_active=bool(data.get("is_active", True)),
            notes=data.get("notes"),
            created_at=created_at,
            synced=bool(data.get("synced", False)),
        )
    
    def format_display(self) -> str:
        """Format subscription for Telegram display."""
        # Status emoji and text
        status_map = {
            "active": ("✅", "Aktif"),
            "expiring_soon": ("⚠️", "Segera Berakhir"),
            "expired": ("❌", "Kadaluarsa"),
        }
        status_emoji, status_text = status_map.get(self.status, ("📦", "Unknown"))
        
        # Category emoji mapping
        category_emojis = {
            "streaming": "🎬",
            "hosting": "🖥️",
            "domain": "🌐",
            "software": "💿",
            "other": "📦",
        }
        cat_emoji = category_emojis.get(self.category.lower(), "📦")
        
        # Format amount with thousand separator
        amount_str = f"{self.amount:,.0f}".replace(",", ".")
        
        # Format dates
        start_str = self.start_date.strftime("%d %b %Y")
        end_str = self.end_date.strftime("%d %b %Y")
        
        # Days remaining text
        if self.status == "expired":
            days_text = "Sudah berakhir"
        elif self.days_remaining == 0:
            days_text = "Berakhir hari ini!"
        elif self.days_remaining == 1:
            days_text = "1 hari lagi"
        else:
            days_text = f"{self.days_remaining} hari lagi"
        
        result = (
            f"{cat_emoji} *{self.name}*\n"
            f"💵 *Biaya:* `Rp {amount_str}`\n"
            f"📁 *Kategori:* {self.category.title()}\n"
            f"📅 *Mulai:* {start_str}\n"
            f"📅 *Berakhir:* {end_str}\n"
            f"⏳ *Sisa:* {days_text}\n"
            f"{status_emoji} *Status:* {status_text}\n"
            f"🆔 *ID:* `{self.id}`"
        )
        
        if self.notes:
            result += f"\n📝 *Catatan:* {self.notes}"
        
        return result
    
    def format_short(self) -> str:
        """Format subscription for short display (list view)."""
        status_emoji = {"active": "✅", "expiring_soon": "⚠️", "expired": "❌"}.get(self.status, "📦")
        amount_str = f"{self.amount:,.0f}".replace(",", ".")
        
        # Truncate name if too long
        name = self.name[:15] + ".." if len(self.name) > 15 else self.name
        
        return f"{status_emoji} {name} │ Rp {amount_str} │ {self.days_remaining}d │ ID: `{self.id}`"
