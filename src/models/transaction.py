from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


EXPENSE_CATEGORIES = [
    "makanan", "transportasi", "belanja", "tagihan",
    "hiburan", "kesehatan", "pendidikan", "lainnya"
]

INCOME_CATEGORIES = [
    "gaji", "bonus", "freelance", "investasi", "hadiah", "lainnya"
]


@dataclass
class Transaction:
    """Model representing a financial transaction."""
    
    user_id: int
    type: str  # "income" or "expense"
    amount: float
    category: str
    description: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    synced: bool = False
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary for database storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "synced": self.synced,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Create Transaction from database row dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
            
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            type=data["type"],
            amount=float(data["amount"]),
            category=data["category"],
            description=data.get("description", ""),
            created_at=created_at,
            synced=bool(data.get("synced", False)),
        )

    
    def format_display(self) -> str:
        """Format transaction for Telegram display."""
        sign = "+" if self.type == "income" else "-"
        
        # Format amount with thousand separator
        amount_str = f"{self.amount:,.0f}".replace(",", ".")
        
        # Format date
        date_str = self.created_at.strftime("%d %b %Y, %H:%M")
        
        # Category emoji mapping
        category_emojis = {
            "makanan": "🍔",
            "transportasi": "🚗",
            "belanja": "🛒",
            "tagihan": "📄",
            "hiburan": "🎮",
            "kesehatan": "💊",
            "pendidikan": "📚",
            "gaji": "💼",
            "bonus": "🎁",
            "freelance": "💻",
            "investasi": "📈",
            "hadiah": "🎀",
            "lainnya": "📦",
        }
        cat_emoji = category_emojis.get(self.category.lower(), "📦")
        
        return (
            f"{cat_emoji} *Kategori:* {self.category.title()}\n"
            f"💵 *Jumlah:* `{sign}Rp {amount_str}`\n"
            f"📝 *Keterangan:* {self.description}\n"
            f"📅 *Tanggal:* {date_str}\n"
            f"🆔 *ID:* `{self.id}`"
        )
    
    def format_short(self) -> str:
        """Format transaction for short display (list view)."""
        type_emoji = "💰" if self.type == "income" else "💸"
        sign = "+" if self.type == "income" else "-"
        amount_str = f"{self.amount:,.0f}".replace(",", ".")
        date_str = self.created_at.strftime("%d/%m")
        
        # Truncate description if too long
        desc = self.description[:12] + ".." if len(self.description) > 12 else self.description
        
        return f"{type_emoji} {date_str} │ {desc} │ {sign}Rp {amount_str} │ ID: `{self.id}`"
