import sqlite3
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.transaction import Transaction
from src.models.user_preference import UserPreference
from src.models.subscription import Subscription
from src.models.bot_user import BotUser
from src.models.subscription_plan import SubscriptionPlan
from src.models.user_subscription import UserSubscription
from src.models.admin_session import AdminSession

logger = logging.getLogger(__name__)


def generate_unique_id() -> int:
    """Generate a unique 5-digit transaction ID."""
    return random.randint(10000, 99999)


class SQLiteDB:
    """SQLite database handler for local storage."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_directory()
        self.init_tables()
    
    def _ensure_directory(self) -> None:
        """Ensure database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def init_tables(self) -> None:
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    synced INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON transactions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON transactions(created_at)")
            
            # User preferences table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Subscriptions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL DEFAULT 'other',
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    synced INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sub_user_id ON subscriptions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sub_end_date ON subscriptions(end_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sub_category ON subscriptions(category)")
            
            # Bot users table (for admin dashboard)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_blocked INTEGER DEFAULT 0,
                    subscription_plan_id INTEGER,
                    subscription_plan_name TEXT DEFAULT 'Free',
                    hourly_query_limit INTEGER DEFAULT 5,
                    daily_query_limit INTEGER DEFAULT 10,
                    monthly_query_limit INTEGER DEFAULT 300,
                    hourly_queries_used INTEGER DEFAULT 0,
                    daily_queries_used INTEGER DEFAULT 0,
                    monthly_queries_used INTEGER DEFAULT 0,
                    total_queries INTEGER DEFAULT 0,
                    last_hourly_reset TEXT,
                    last_query_reset TEXT,
                    last_monthly_reset TEXT,
                    reset_hours INTEGER DEFAULT 1
                )
            """)
            
            # Add new columns if they don't exist (migration)
            try:
                conn.execute("ALTER TABLE bot_users ADD COLUMN hourly_query_limit INTEGER DEFAULT 5")
            except:
                pass
            try:
                conn.execute("ALTER TABLE bot_users ADD COLUMN hourly_queries_used INTEGER DEFAULT 0")
            except:
                pass
            try:
                conn.execute("ALTER TABLE bot_users ADD COLUMN last_hourly_reset TEXT")
            except:
                pass
            try:
                conn.execute("ALTER TABLE bot_users ADD COLUMN reset_hours INTEGER DEFAULT 1")
            except:
                pass
            try:
                conn.execute("ALTER TABLE bot_users ADD COLUMN subscription_plan_name TEXT DEFAULT 'Free'")
            except:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bot_users_username ON bot_users(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bot_users_registered ON bot_users(registered_at)")
            
            # Subscription plans table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscription_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    daily_query_limit INTEGER DEFAULT 10,
                    monthly_query_limit INTEGER DEFAULT 300,
                    price REAL DEFAULT 0,
                    duration_days INTEGER DEFAULT 30,
                    features TEXT DEFAULT '[]',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User subscriptions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_id INTEGER NOT NULL,
                    plan_name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    assigned_by TEXT DEFAULT 'system',
                    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES bot_users(user_id),
                    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_subs_user ON user_subscriptions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_subs_status ON user_subscriptions(status)")
            
            # Admin sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    token TEXT PRIMARY KEY,
                    admin_username TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT NOT NULL,
                    is_valid INTEGER DEFAULT 1
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at)")
            
            conn.commit()

    
    def _generate_unique_transaction_id(self) -> int:
        """Generate a unique 5-digit transaction ID that doesn't exist in DB."""
        with self._get_connection() as conn:
            for _ in range(100):  # Max 100 attempts
                new_id = generate_unique_id()
                cursor = conn.execute("SELECT id FROM transactions WHERE id = ?", (new_id,))
                if cursor.fetchone() is None:
                    return new_id
            # Fallback to 6-digit if 5-digit exhausted
            return random.randint(100000, 999999)
    
    def insert_transaction(self, transaction: Transaction) -> int:
        """Insert transaction with unique ID and return its ID."""
        unique_id = self._generate_unique_transaction_id()
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transactions (id, user_id, type, amount, category, description, created_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    unique_id,
                    transaction.user_id,
                    transaction.type,
                    transaction.amount,
                    transaction.category,
                    transaction.description,
                    transaction.created_at.isoformat(),
                    0,
                )
            )
            conn.commit()
            return unique_id
    
    def get_transactions(self, user_id: int, limit: int = 10) -> list[Transaction]:
        """Get transactions for user, ordered by newest first."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return [Transaction.from_dict(dict(row)) for row in rows]
    
    def get_transaction_by_id(self, user_id: int, transaction_id: int) -> Optional[Transaction]:
        """Get single transaction by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM transactions WHERE id = ? AND user_id = ?",
                (transaction_id, user_id)
            )
            row = cursor.fetchone()
            if row:
                return Transaction.from_dict(dict(row))
            return None
    
    def delete_transaction(self, user_id: int, transaction_id: int) -> bool:
        """Delete transaction by ID. Returns True if deleted."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM transactions WHERE id = ? AND user_id = ?",
                (transaction_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_summary(self, user_id: int, month: int, year: int) -> dict:
        """Get monthly summary for user."""
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"
        
        with self._get_connection() as conn:
            # Get income total
            cursor = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions 
                WHERE user_id = ? AND type = 'income'
                AND created_at >= ? AND created_at < ?
                """,
                (user_id, start_date, end_date)
            )
            income = cursor.fetchone()["total"]
            
            # Get expense total
            cursor = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions 
                WHERE user_id = ? AND type = 'expense'
                AND created_at >= ? AND created_at < ?
                """,
                (user_id, start_date, end_date)
            )
            expense = cursor.fetchone()["total"]
            
            return {
                "income": income,
                "expense": expense,
                "balance": income - expense,
                "month": month,
                "year": year,
            }
    
    def mark_synced(self, transaction_id: int) -> None:
        """Mark transaction as synced to cloud."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE transactions SET synced = 1 WHERE id = ?",
                (transaction_id,)
            )
            conn.commit()
    
    def get_pending_sync(self) -> list[Transaction]:
        """Get transactions not yet synced to cloud."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM transactions WHERE synced = 0 ORDER BY created_at ASC"
            )
            rows = cursor.fetchall()
            return [Transaction.from_dict(dict(row)) for row in rows]

    # User Preference methods
    
    def save_user_preference(self, user_id: int, provider: str, model: Optional[str] = None) -> bool:
        """Save or update user's AI provider preference."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO user_preferences (user_id, provider, model, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        provider = excluded.provider,
                        model = excluded.model,
                        updated_at = excluded.updated_at
                    """,
                    (user_id, provider, model, datetime.now().isoformat())
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save user preference: {e}")
            return False
    
    def get_user_preference(self, user_id: int) -> Optional[UserPreference]:
        """Get user's AI provider preference."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return UserPreference.from_dict(dict(row))
            return None
    
    def get_all_transactions(self, user_id: int) -> list[Transaction]:
        """Get all transactions for user, ordered by newest first."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            rows = cursor.fetchall()
            return [Transaction.from_dict(dict(row)) for row in rows]
    
    def get_transactions_by_month(self, user_id: int, month: int, year: int) -> list[Transaction]:
        """Get transactions for a specific month."""
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM transactions 
                WHERE user_id = ? AND created_at >= ? AND created_at < ?
                ORDER BY created_at DESC
                """,
                (user_id, start_date, end_date)
            )
            rows = cursor.fetchall()
            return [Transaction.from_dict(dict(row)) for row in rows]

    # Subscription methods
    
    def _generate_unique_subscription_id(self) -> int:
        """Generate a unique 5-digit subscription ID that doesn't exist in DB."""
        with self._get_connection() as conn:
            for _ in range(100):
                new_id = generate_unique_id()
                cursor = conn.execute("SELECT id FROM subscriptions WHERE id = ?", (new_id,))
                if cursor.fetchone() is None:
                    return new_id
            return random.randint(100000, 999999)
    
    def insert_subscription(self, subscription: Subscription) -> int:
        """Insert subscription with unique ID and return its ID."""
        unique_id = self._generate_unique_subscription_id()
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO subscriptions (id, user_id, name, amount, category, start_date, end_date, is_active, notes, created_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    unique_id,
                    subscription.user_id,
                    subscription.name,
                    subscription.amount,
                    subscription.category,
                    subscription.start_date.isoformat(),
                    subscription.end_date.isoformat(),
                    1 if subscription.is_active else 0,
                    subscription.notes,
                    subscription.created_at.isoformat(),
                    0,
                )
            )
            conn.commit()
            return unique_id
    
    def get_subscriptions(self, user_id: int, include_expired: bool = False) -> list[Subscription]:
        """Get subscriptions for user."""
        with self._get_connection() as conn:
            if include_expired:
                cursor = conn.execute(
                    "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY end_date ASC",
                    (user_id,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM subscriptions WHERE user_id = ? AND is_active = 1 ORDER BY end_date ASC",
                    (user_id,)
                )
            rows = cursor.fetchall()
            return [Subscription.from_dict(dict(row)) for row in rows]
    
    def get_subscription_by_id(self, user_id: int, subscription_id: int) -> Optional[Subscription]:
        """Get single subscription by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM subscriptions WHERE id = ? AND user_id = ?",
                (subscription_id, user_id)
            )
            row = cursor.fetchone()
            if row:
                return Subscription.from_dict(dict(row))
            return None
    
    def delete_subscription(self, user_id: int, subscription_id: int) -> bool:
        """Delete subscription by ID. Returns True if deleted."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM subscriptions WHERE id = ? AND user_id = ?",
                (subscription_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update_subscription_end_date(self, user_id: int, subscription_id: int, new_end_date) -> bool:
        """Update subscription end date (for renewal). Returns True if updated."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE subscriptions SET end_date = ?, is_active = 1 WHERE id = ? AND user_id = ?",
                (new_end_date.isoformat(), subscription_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_expiring_subscriptions(self, user_id: int, days: int = 7) -> list[Subscription]:
        """Get subscriptions expiring within specified days."""
        from datetime import date, timedelta
        today = date.today()
        end_threshold = today + timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND is_active = 1 
                AND end_date >= ? AND end_date <= ?
                ORDER BY end_date ASC
                """,
                (user_id, today.isoformat(), end_threshold.isoformat())
            )
            rows = cursor.fetchall()
            return [Subscription.from_dict(dict(row)) for row in rows]
    
    def mark_subscription_synced(self, subscription_id: int) -> None:
        """Mark subscription as synced to cloud."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE subscriptions SET synced = 1 WHERE id = ?",
                (subscription_id,)
            )
            conn.commit()
    
    def get_pending_subscription_sync(self) -> list[Subscription]:
        """Get subscriptions not yet synced to cloud."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM subscriptions WHERE synced = 0 ORDER BY created_at ASC"
            )
            rows = cursor.fetchall()
            return [Subscription.from_dict(dict(row)) for row in rows]

    # ==================== Bot User Methods ====================
    
    def register_bot_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> BotUser:
        """Register or update a bot user."""
        with self._get_connection() as conn:
            now = datetime.now().isoformat()
            conn.execute(
                """
                INSERT INTO bot_users (user_id, username, first_name, registered_at, last_active)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = COALESCE(excluded.username, bot_users.username),
                    first_name = COALESCE(excluded.first_name, bot_users.first_name),
                    last_active = excluded.last_active
                """,
                (user_id, username, first_name, now, now)
            )
            conn.commit()
        return self.get_bot_user(user_id)
    
    def get_bot_user(self, user_id: int) -> Optional[BotUser]:
        """Get a bot user by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM bot_users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return BotUser.from_dict(dict(row))
            return None
    
    def get_all_bot_users(self, page: int = 1, per_page: int = 20, search: Optional[str] = None) -> tuple[list[BotUser], int]:
        """Get paginated list of bot users with optional search."""
        offset = (page - 1) * per_page
        
        with self._get_connection() as conn:
            if search:
                search_pattern = f"%{search}%"
                cursor = conn.execute(
                    """
                    SELECT * FROM bot_users 
                    WHERE username LIKE ? OR first_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?
                    ORDER BY registered_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (search_pattern, search_pattern, search_pattern, per_page, offset)
                )
                count_cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM bot_users 
                    WHERE username LIKE ? OR first_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?
                    """,
                    (search_pattern, search_pattern, search_pattern)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM bot_users ORDER BY registered_at DESC LIMIT ? OFFSET ?",
                    (per_page, offset)
                )
                count_cursor = conn.execute("SELECT COUNT(*) FROM bot_users")
            
            rows = cursor.fetchall()
            total = count_cursor.fetchone()[0]
            
            return [BotUser.from_dict(dict(row)) for row in rows], total
    
    def update_bot_user_activity(self, user_id: int) -> None:
        """Update user's last active timestamp."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET last_active = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
    
    def block_bot_user(self, user_id: int) -> bool:
        """Block a bot user."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE bot_users SET is_blocked = 1 WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def unblock_bot_user(self, user_id: int) -> bool:
        """Unblock a bot user."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE bot_users SET is_blocked = 0 WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_bot_user(self, user_id: int) -> bool:
        """Delete a bot user and all related data."""
        with self._get_connection() as conn:
            # Delete user subscriptions
            conn.execute("DELETE FROM user_subscriptions WHERE user_id = ?", (user_id,))
            # Delete transactions
            conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            # Delete subscriptions (service subscriptions)
            conn.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
            # Delete user preferences
            conn.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
            # Delete bot user
            cursor = conn.execute("DELETE FROM bot_users WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def reset_bot_user_data(self, user_id: int) -> dict:
        """Reset user data (delete transactions, subscriptions) but keep user account."""
        with self._get_connection() as conn:
            # Count data before deletion
            tx_count = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            sub_count = conn.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            user_sub_count = conn.execute(
                "SELECT COUNT(*) FROM user_subscriptions WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            
            # Delete transactions
            conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            # Delete subscriptions (service subscriptions)
            conn.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
            # Delete user subscriptions (plan subscriptions)
            conn.execute("DELETE FROM user_subscriptions WHERE user_id = ?", (user_id,))
            
            # Reset query counters
            conn.execute(
                """
                UPDATE bot_users 
                SET daily_queries_used = 0, 
                    monthly_queries_used = 0, 
                    total_queries = 0,
                    subscription_plan_id = NULL
                WHERE user_id = ?
                """,
                (user_id,)
            )
            conn.commit()
            
            return {
                "transactions_deleted": tx_count,
                "subscriptions_deleted": sub_count,
                "user_subscriptions_deleted": user_sub_count,
            }
    
    def get_bot_user_stats(self) -> dict:
        """Get bot user statistics."""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM bot_users").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM bot_users WHERE is_blocked = 0"
            ).fetchone()[0]
            blocked = conn.execute(
                "SELECT COUNT(*) FROM bot_users WHERE is_blocked = 1"
            ).fetchone()[0]
            
            return {
                "total_users": total,
                "active_users": active,
                "blocked_users": blocked,
            }
    
    def update_bot_user_limits(self, user_id: int, daily_limit: int, monthly_limit: int) -> bool:
        """Update user's query limits."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE bot_users 
                SET daily_query_limit = ?, monthly_query_limit = ?
                WHERE user_id = ?
                """,
                (daily_limit, monthly_limit, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_user_query_count(self, user_id: int) -> None:
        """Increment user's query counters."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE bot_users 
                SET daily_queries_used = daily_queries_used + 1,
                    monthly_queries_used = monthly_queries_used + 1,
                    total_queries = total_queries + 1
                WHERE user_id = ?
                """,
                (user_id,)
            )
            conn.commit()
    
    def reset_daily_query_counts(self) -> int:
        """Reset daily query counts for all users. Returns number of users reset."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE bot_users 
                SET daily_queries_used = 0, last_query_reset = ?
                """,
                (datetime.now().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount
    
    def reset_monthly_query_counts(self) -> int:
        """Reset monthly query counts for all users. Returns number of users reset."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE bot_users 
                SET monthly_queries_used = 0, last_monthly_reset = ?
                """,
                (datetime.now().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount
    
    # ==================== Subscription Plan Methods ====================
    
    def create_subscription_plan(self, plan: SubscriptionPlan) -> int:
        """Create a new subscription plan."""
        with self._get_connection() as conn:
            # Add columns if they don't exist (migration)
            try:
                conn.execute("ALTER TABLE subscription_plans ADD COLUMN hourly_query_limit INTEGER DEFAULT 5")
            except:
                pass
            try:
                conn.execute("ALTER TABLE subscription_plans ADD COLUMN reset_hours INTEGER DEFAULT 1")
            except:
                pass
            
            cursor = conn.execute(
                """
                INSERT INTO subscription_plans (name, hourly_query_limit, daily_query_limit, monthly_query_limit, reset_hours, price, duration_days, features, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.name,
                    plan.hourly_query_limit,
                    plan.daily_query_limit,
                    plan.monthly_query_limit,
                    plan.reset_hours,
                    plan.price,
                    plan.duration_days,
                    plan.to_dict()["features"],
                    1 if plan.is_active else 0,
                    plan.created_at.isoformat(),
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_subscription_plan(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """Get a subscription plan by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM subscription_plans WHERE id = ?", (plan_id,))
            row = cursor.fetchone()
            if row:
                return SubscriptionPlan.from_dict(dict(row))
            return None
    
    def get_all_subscription_plans(self, active_only: bool = True) -> list[SubscriptionPlan]:
        """Get all subscription plans."""
        with self._get_connection() as conn:
            if active_only:
                cursor = conn.execute("SELECT * FROM subscription_plans WHERE is_active = 1 ORDER BY price ASC")
            else:
                cursor = conn.execute("SELECT * FROM subscription_plans ORDER BY price ASC")
            rows = cursor.fetchall()
            return [SubscriptionPlan.from_dict(dict(row)) for row in rows]
    
    def update_subscription_plan(self, plan_id: int, **kwargs) -> bool:
        """Update a subscription plan."""
        if not kwargs:
            return False
        
        set_clauses = []
        values = []
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        values.append(plan_id)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE subscription_plans SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_subscription_plan(self, plan_id: int) -> bool:
        """Delete a subscription plan."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM subscription_plans WHERE id = ?", (plan_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== User Subscription Methods ====================
    
    def assign_user_subscription(self, subscription: UserSubscription) -> int:
        """Assign a subscription to a user."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO user_subscriptions (user_id, plan_id, plan_name, start_date, end_date, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscription.user_id,
                    subscription.plan_id,
                    subscription.plan_name,
                    subscription.start_date.isoformat(),
                    subscription.end_date.isoformat(),
                    subscription.status,
                    subscription.assigned_by,
                    subscription.assigned_at.isoformat(),
                )
            )
            # Update user's subscription plan ID
            conn.execute(
                "UPDATE bot_users SET subscription_plan_id = ? WHERE user_id = ?",
                (subscription.plan_id, subscription.user_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_subscription(self, user_id: int) -> Optional[UserSubscription]:
        """Get user's current active subscription."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM user_subscriptions 
                WHERE user_id = ? AND status = 'active'
                ORDER BY end_date DESC LIMIT 1
                """,
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return UserSubscription.from_dict(dict(row))
            return None
    
    def get_user_subscription_history(self, user_id: int) -> list[UserSubscription]:
        """Get user's subscription history."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_subscriptions WHERE user_id = ? ORDER BY assigned_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [UserSubscription.from_dict(dict(row)) for row in rows]
    
    def expire_user_subscriptions(self) -> int:
        """Mark expired subscriptions. Returns count of expired."""
        from datetime import date
        today = date.today().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE user_subscriptions 
                SET status = 'expired'
                WHERE status = 'active' AND end_date < ?
                """,
                (today,)
            )
            conn.commit()
            return cursor.rowcount
    
    def get_active_subscriptions_count(self) -> int:
        """Get count of active subscriptions."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active'"
            )
            return cursor.fetchone()[0]
    
    # ==================== Admin Session Methods ====================
    
    def create_admin_session(self, session: AdminSession) -> str:
        """Create a new admin session."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO admin_sessions (token, admin_username, created_at, expires_at, is_valid)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session.token,
                    session.admin_username,
                    session.created_at.isoformat(),
                    session.expires_at.isoformat(),
                    1 if session.is_valid else 0,
                )
            )
            conn.commit()
            return session.token
    
    def get_admin_session(self, token: str) -> Optional[AdminSession]:
        """Get an admin session by token."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM admin_sessions WHERE token = ?", (token,))
            row = cursor.fetchone()
            if row:
                return AdminSession.from_dict(dict(row))
            return None
    
    def invalidate_admin_session(self, token: str) -> bool:
        """Invalidate an admin session."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE admin_sessions SET is_valid = 0 WHERE token = ?",
                (token,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def refresh_admin_session(self, token: str, new_expires_at: datetime) -> bool:
        """Refresh an admin session's expiration time."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE admin_sessions SET expires_at = ? WHERE token = ? AND is_valid = 1",
                (new_expires_at.isoformat(), token)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired admin sessions. Returns count of removed."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM admin_sessions WHERE expires_at < ? OR is_valid = 0",
                (datetime.now().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount
    
    # ==================== Analytics Methods ====================
    
    def get_daily_query_stats(self, days: int = 30) -> list[dict]:
        """Get daily query statistics for the past N days."""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM transactions
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date ASC
                """,
                (start_date.isoformat(),)
            )
            rows = cursor.fetchall()
            return [{"date": row["date"], "count": row["count"]} for row in rows]
    
    def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics."""
        user_stats = self.get_bot_user_stats()
        active_subs = self.get_active_subscriptions_count()
        
        with self._get_connection() as conn:
            # Today's queries
            from datetime import date
            today = date.today().isoformat()
            cursor = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE DATE(created_at) = ?",
                (today,)
            )
            today_queries = cursor.fetchone()[0]
            
            # Total transactions
            cursor = conn.execute("SELECT COUNT(*) FROM transactions")
            total_transactions = cursor.fetchone()[0]
        
        return {
            **user_stats,
            "active_subscriptions": active_subs,
            "today_queries": today_queries,
            "total_transactions": total_transactions,
        }
