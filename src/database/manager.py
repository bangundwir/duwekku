import logging
from typing import Optional

from src.models.transaction import Transaction
from .sqlite_db import SQLiteDB
from .tidb_db import TiDBCloud

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages dual database operations (SQLite + TiDB Cloud)."""
    
    def __init__(self, sqlite_db: SQLiteDB, tidb_db: Optional[TiDBCloud] = None):
        self.sqlite = sqlite_db
        self.tidb = tidb_db
    
    def save_transaction(self, transaction: Transaction) -> Optional[Transaction]:
        """
        Save transaction to SQLite first, then sync to TiDB.
        Returns the saved transaction with ID, or None if failed.
        """
        try:
            # Save to SQLite first (primary storage)
            transaction_id = self.sqlite.insert_transaction(transaction)
            transaction.id = transaction_id
            
            # Try to sync to TiDB Cloud
            if self.tidb:
                if self.tidb.insert_transaction(transaction):
                    self.sqlite.mark_synced(transaction_id)
                    transaction.synced = True
                else:
                    logger.warning(f"Failed to sync transaction {transaction_id} to TiDB")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to save transaction: {e}")
            return None
    
    def get_transactions(self, user_id: int, limit: int = 10) -> list[Transaction]:
        """Get transactions from SQLite."""
        try:
            return self.sqlite.get_transactions(user_id, limit)
        except Exception as e:
            logger.error(f"Failed to get transactions: {e}")
            return []
    
    def get_transaction_by_id(self, user_id: int, transaction_id: int) -> Optional[Transaction]:
        """Get single transaction by ID."""
        try:
            return self.sqlite.get_transaction_by_id(user_id, transaction_id)
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
            return None

    
    def get_summary(self, user_id: int, month: int, year: int) -> dict:
        """Get monthly summary."""
        try:
            return self.sqlite.get_summary(user_id, month, year)
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return {"income": 0, "expense": 0, "balance": 0, "month": month, "year": year}
    
    def delete_transaction(self, user_id: int, transaction_id: int) -> bool:
        """Delete transaction from both databases."""
        try:
            # Delete from SQLite
            deleted = self.sqlite.delete_transaction(user_id, transaction_id)
            
            if deleted and self.tidb:
                # Also delete from TiDB
                self.tidb.delete_transaction(transaction_id)
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete transaction: {e}")
            return False
    
    def sync_pending(self) -> int:
        """
        Sync pending transactions to TiDB Cloud.
        Returns number of successfully synced transactions.
        """
        if not self.tidb:
            return 0
        
        synced_count = 0
        try:
            pending = self.sqlite.get_pending_sync()
            logger.info(f"Found {len(pending)} pending transactions to sync")
            
            for transaction in pending:
                if self.tidb.insert_transaction(transaction):
                    self.sqlite.mark_synced(transaction.id)
                    synced_count += 1
                    logger.debug(f"Synced transaction {transaction.id}")
                else:
                    logger.warning(f"Failed to sync transaction {transaction.id}")
            
            logger.info(f"Synced {synced_count}/{len(pending)} transactions")
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
        
        return synced_count
    
    def get_all_transactions(self, user_id: int) -> list[Transaction]:
        """Get all transactions for user."""
        try:
            return self.sqlite.get_all_transactions(user_id)
        except Exception as e:
            logger.error(f"Failed to get all transactions: {e}")
            return []
    
    def get_transactions_by_month(self, user_id: int, month: int, year: int) -> list[Transaction]:
        """Get transactions for a specific month."""
        try:
            return self.sqlite.get_transactions_by_month(user_id, month, year)
        except Exception as e:
            logger.error(f"Failed to get transactions by month: {e}")
            return []
