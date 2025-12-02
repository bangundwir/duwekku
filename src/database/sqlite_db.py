import sqlite3
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.transaction import Transaction
from src.models.user_preference import UserPreference
from src.models.subscription import Subscription

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
