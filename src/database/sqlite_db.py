import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.transaction import Transaction
from src.models.user_preference import UserPreference

logger = logging.getLogger(__name__)


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
            conn.commit()

    
    def insert_transaction(self, transaction: Transaction) -> int:
        """Insert transaction and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO transactions (user_id, type, amount, category, description, created_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
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
            return cursor.lastrowid
    
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
