# Data Models Documentation

Dokumentasi lengkap untuk data models Money Tracker Bot.

## Overview

Semua model menggunakan Python dataclasses untuk type safety dan serialization.

## Struktur Kode

```
src/models/
├── __init__.py
├── transaction.py        # Transaksi keuangan
├── subscription.py       # Langganan user
├── bot_user.py          # User bot
├── subscription_plan.py  # Paket langganan
├── user_subscription.py  # Subscription user ke plan
├── user_preference.py    # Preferensi user
└── admin_session.py      # Session admin
```

## Transaction

Model untuk transaksi keuangan.

```python
@dataclass
class Transaction:
    user_id: int
    type: str           # "income" atau "expense"
    amount: float
    category: str
    description: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    synced: bool = False
    short_id: Optional[str] = None
```

### Methods
- `to_dict()` - Convert ke dictionary
- `from_dict(data)` - Create dari dictionary
- `format_display()` - Format untuk tampilan
- `format_short()` - Format singkat

## Subscription

Model untuk langganan layanan.

```python
@dataclass
class Subscription:
    user_id: int
    name: str
    amount: float
    category: str       # streaming/hosting/domain/software/other
    start_date: date
    end_date: date
    duration_months: int
    id: Optional[int] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    short_id: Optional[str] = None
```

### Properties
- `status` - Status (active/expiring_soon/expired)
- `days_remaining` - Sisa hari

### Methods
- `to_dict()` - Convert ke dictionary
- `from_dict(data)` - Create dari dictionary
- `format_display()` - Format untuk tampilan

## BotUser

Model untuk user bot.

```python
@dataclass
class BotUser:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    registered_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    is_blocked: bool = False
    subscription_plan_id: Optional[int] = None
    subscription_plan_name: str = "Free"
    hourly_query_limit: int = 5
    hourly_queries_used: int = 0
    daily_query_limit: int = 10
    daily_queries_used: int = 0
    monthly_query_limit: int = 300
    monthly_queries_used: int = 0
    total_queries: int = 0
    reset_hours: int = 1
    last_hourly_reset: Optional[datetime] = None
    last_query_reset: Optional[datetime] = None
    last_monthly_reset: Optional[datetime] = None
```

### Properties
- `hourly_queries_remaining` - Sisa query per jam
- `daily_queries_remaining` - Sisa query per hari
- `monthly_queries_remaining` - Sisa query per bulan

### Methods
- `to_dict()` - Convert ke dictionary
- `from_dict(data)` - Create dari dictionary
- `get_reset_time_remaining()` - Waktu sampai reset

## SubscriptionPlan

Model untuk paket langganan.

```python
@dataclass
class SubscriptionPlan:
    name: str
    daily_query_limit: int
    monthly_query_limit: int
    price: float
    duration_days: int
    id: Optional[int] = None
    hourly_query_limit: int = 5
    reset_hours: int = 1
    features: List[str] = field(default_factory=list)
    is_active: bool = True
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.now)
```

### Methods
- `to_dict()` - Convert ke dictionary
- `from_dict(data)` - Create dari dictionary
- `format_price()` - Format harga (Rp)
- `format_duration()` - Format durasi

### Default Plans
```python
DEFAULT_PLANS = [
    SubscriptionPlan(name="Free", hourly=5, daily=10, monthly=100, price=0, is_default=True),
    SubscriptionPlan(name="Basic", hourly=20, daily=50, monthly=500, price=25000),
    SubscriptionPlan(name="Premium", hourly=50, daily=200, monthly=2000, price=75000),
    SubscriptionPlan(name="Pro", hourly=200, daily=1000, monthly=10000, price=150000),
]
```

## UserSubscription

Model untuk subscription user ke plan.

```python
@dataclass
class UserSubscription:
    user_id: int
    plan_id: int
    plan_name: str
    start_date: date
    end_date: date
    id: Optional[int] = None
    status: str = "active"
    assigned_by: str = "system"
    assigned_at: datetime = field(default_factory=datetime.now)
```

### Properties
- `days_remaining` - Sisa hari
- `is_expired` - Apakah sudah expired

## UserPreference

Model untuk preferensi user.

```python
@dataclass
class UserPreference:
    user_id: int
    ai_provider: str = "groq"
    ai_model: str = "llama-3.3-70b-versatile"
    updated_at: datetime = field(default_factory=datetime.now)
```

## AdminSession

Model untuk session admin dashboard.

```python
@dataclass
class AdminSession:
    token: str
    admin_username: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
```

### Properties
- `is_expired` - Apakah session expired

## Serialization

Semua model mendukung:

### to_dict()
Convert model ke dictionary untuk database storage.
```python
transaction = Transaction(...)
data = transaction.to_dict()
```

### from_dict()
Create model dari dictionary (database row).
```python
data = {"user_id": 123, "type": "expense", ...}
transaction = Transaction.from_dict(data)
```

## Type Safety

Menggunakan Python type hints untuk:
- IDE autocomplete
- Static type checking
- Documentation
- Runtime validation (dengan dataclasses)
