import pytest
from datetime import datetime

from src.models.transaction import Transaction


class TestSQLiteDB:
    """Tests for SQLite database operations."""
    
    def test_insert_and_get_transaction(self, sqlite_db, sample_transaction):
        """Test inserting and retrieving a transaction."""
        # Insert
        transaction_id = sqlite_db.insert_transaction(sample_transaction)
        assert transaction_id > 0
        
        # Retrieve
        transactions = sqlite_db.get_transactions(sample_transaction.user_id, limit=10)
        assert len(transactions) == 1
        assert transactions[0].id == transaction_id
        assert transactions[0].amount == 50000
        assert transactions[0].category == "makanan"
    
    def test_get_transaction_by_id(self, sqlite_db, sample_transaction):
        """Test getting transaction by ID."""
        transaction_id = sqlite_db.insert_transaction(sample_transaction)
        
        # Get by ID
        transaction = sqlite_db.get_transaction_by_id(
            sample_transaction.user_id, 
            transaction_id
        )
        assert transaction is not None
        assert transaction.id == transaction_id
        
        # Non-existent ID
        transaction = sqlite_db.get_transaction_by_id(
            sample_transaction.user_id, 
            99999
        )
        assert transaction is None
    
    def test_delete_transaction(self, sqlite_db, sample_transaction):
        """Test deleting a transaction."""
        transaction_id = sqlite_db.insert_transaction(sample_transaction)
        
        # Delete
        result = sqlite_db.delete_transaction(sample_transaction.user_id, transaction_id)
        assert result is True
        
        # Verify deleted
        transaction = sqlite_db.get_transaction_by_id(
            sample_transaction.user_id, 
            transaction_id
        )
        assert transaction is None
    
    def test_delete_nonexistent(self, sqlite_db):
        """Test deleting non-existent transaction."""
        result = sqlite_db.delete_transaction(123456, 99999)
        assert result is False

    
    def test_get_summary(self, sqlite_db):
        """Test monthly summary calculation."""
        user_id = 123456
        now = datetime.now()
        
        # Add income
        income = Transaction(
            user_id=user_id,
            type="income",
            amount=5000000,
            category="gaji",
            description="gaji",
            created_at=now,
        )
        sqlite_db.insert_transaction(income)
        
        # Add expenses
        expense1 = Transaction(
            user_id=user_id,
            type="expense",
            amount=100000,
            category="makanan",
            description="makan",
            created_at=now,
        )
        sqlite_db.insert_transaction(expense1)
        
        expense2 = Transaction(
            user_id=user_id,
            type="expense",
            amount=200000,
            category="transportasi",
            description="bensin",
            created_at=now,
        )
        sqlite_db.insert_transaction(expense2)
        
        # Get summary
        summary = sqlite_db.get_summary(user_id, now.month, now.year)
        
        assert summary["income"] == 5000000
        assert summary["expense"] == 300000
        assert summary["balance"] == 4700000
    
    def test_mark_synced(self, sqlite_db, sample_transaction):
        """Test marking transaction as synced."""
        transaction_id = sqlite_db.insert_transaction(sample_transaction)
        
        # Initially not synced
        pending = sqlite_db.get_pending_sync()
        assert len(pending) == 1
        
        # Mark as synced
        sqlite_db.mark_synced(transaction_id)
        
        # Should not be in pending anymore
        pending = sqlite_db.get_pending_sync()
        assert len(pending) == 0
    
    def test_transactions_ordered_by_newest(self, sqlite_db):
        """Test that transactions are ordered by newest first."""
        user_id = 123456
        
        # Insert multiple transactions
        for i in range(5):
            t = Transaction(
                user_id=user_id,
                type="expense",
                amount=(i + 1) * 10000,
                category="test",
                description=f"transaction {i}",
                created_at=datetime.now(),
            )
            sqlite_db.insert_transaction(t)
        
        # Get transactions
        transactions = sqlite_db.get_transactions(user_id, limit=10)
        
        # Should be ordered by newest first (highest amount last inserted)
        assert len(transactions) == 5
        assert transactions[0].amount == 50000  # Last inserted
        assert transactions[4].amount == 10000  # First inserted


class TestDatabaseManager:
    """Tests for DatabaseManager."""
    
    def test_save_transaction(self, db_manager, sample_transaction):
        """Test saving transaction through manager."""
        saved = db_manager.save_transaction(sample_transaction)
        
        assert saved is not None
        assert saved.id is not None
        assert saved.amount == 50000
    
    def test_get_transactions(self, db_manager, sample_transaction):
        """Test getting transactions through manager."""
        db_manager.save_transaction(sample_transaction)
        
        transactions = db_manager.get_transactions(sample_transaction.user_id)
        assert len(transactions) == 1
    
    def test_delete_transaction(self, db_manager, sample_transaction):
        """Test deleting transaction through manager."""
        saved = db_manager.save_transaction(sample_transaction)
        
        result = db_manager.delete_transaction(saved.user_id, saved.id)
        assert result is True
        
        # Verify deleted
        transaction = db_manager.get_transaction_by_id(saved.user_id, saved.id)
        assert transaction is None
