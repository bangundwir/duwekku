import pytest
from datetime import datetime

from src.models.transaction import Transaction


class TestTransaction:
    """Tests for Transaction model."""
    
    def test_to_dict(self, sample_transaction):
        """Test transaction serialization to dict."""
        data = sample_transaction.to_dict()
        
        assert data["user_id"] == 123456
        assert data["type"] == "expense"
        assert data["amount"] == 50000
        assert data["category"] == "makanan"
        assert data["description"] == "beli makan siang"
        assert "created_at" in data
    
    def test_from_dict(self):
        """Test transaction deserialization from dict."""
        data = {
            "id": 1,
            "user_id": 123456,
            "type": "income",
            "amount": 5000000,
            "category": "gaji",
            "description": "gaji bulanan",
            "created_at": "2024-01-15T10:30:00",
            "synced": True,
        }
        
        transaction = Transaction.from_dict(data)
        
        assert transaction.id == 1
        assert transaction.user_id == 123456
        assert transaction.type == "income"
        assert transaction.amount == 5000000
        assert transaction.category == "gaji"
        assert transaction.synced is True
    
    def test_format_display_expense(self, sample_transaction):
        """Test expense transaction display format."""
        sample_transaction.id = 1
        display = sample_transaction.format_display()
        
        assert "Makanan" in display  # Category
        assert "50.000" in display
        assert "beli makan siang" in display
        assert "1" in display  # ID
    
    def test_format_display_income(self, sample_income):
        """Test income transaction display format."""
        sample_income.id = 2
        display = sample_income.format_display()
        
        assert "Gaji" in display  # Category
        assert "5.000.000" in display
    
    def test_format_short(self, sample_transaction):
        """Test short format for list view."""
        sample_transaction.id = 5
        short = sample_transaction.format_short()
        
        assert "5" in short  # ID
        assert "50.000" in short  # Amount
