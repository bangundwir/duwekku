import pytest

from src.ai.parser import normalize_amount, ParsedTransaction


class TestNormalizeAmount:
    """Tests for amount normalization function."""
    
    def test_ribu_suffix(self):
        """Test 'rb' and 'ribu' suffixes."""
        assert normalize_amount("50rb") == 50000
        assert normalize_amount("100ribu") == 100000
        assert normalize_amount("25 rb") == 25000
    
    def test_juta_suffix(self):
        """Test 'jt' and 'juta' suffixes."""
        assert normalize_amount("5jt") == 5000000
        assert normalize_amount("2juta") == 2000000
        assert normalize_amount("1.5jt") == 1500000
    
    def test_k_suffix(self):
        """Test 'k' suffix."""
        assert normalize_amount("100k") == 100000
        assert normalize_amount("50K") == 50000
    
    def test_decimal_amounts(self):
        """Test decimal amounts."""
        assert normalize_amount("1.5jt") == 1500000
        assert normalize_amount("2,5jt") == 2500000
        assert normalize_amount("0.5jt") == 500000
    
    def test_plain_numbers(self):
        """Test plain numbers without suffix."""
        assert normalize_amount("50000") == 50000
        assert normalize_amount("1000000") == 1000000
    
    def test_invalid_input(self):
        """Test invalid inputs."""
        assert normalize_amount("") is None
        assert normalize_amount(None) is None
        assert normalize_amount("abc") is None


class TestParsedTransaction:
    """Tests for ParsedTransaction model."""
    
    def test_valid_expense(self):
        """Test valid expense transaction."""
        parsed = ParsedTransaction(
            type="expense",
            amount=50000,
            category="makanan",
            description="beli makan",
        )
        assert parsed.is_valid() is True
    
    def test_valid_income(self):
        """Test valid income transaction."""
        parsed = ParsedTransaction(
            type="income",
            amount=5000000,
            category="gaji",
            description="gaji bulanan",
        )
        assert parsed.is_valid() is True
    
    def test_invalid_type(self):
        """Test invalid transaction type."""
        parsed = ParsedTransaction(
            type="invalid",
            amount=50000,
            category="makanan",
            description="test",
        )
        assert parsed.is_valid() is False
    
    def test_invalid_amount(self):
        """Test invalid amount (zero or negative)."""
        parsed = ParsedTransaction(
            type="expense",
            amount=0,
            category="makanan",
            description="test",
        )
        assert parsed.is_valid() is False
        
        parsed.amount = -100
        assert parsed.is_valid() is False
    
    def test_empty_category(self):
        """Test empty category."""
        parsed = ParsedTransaction(
            type="expense",
            amount=50000,
            category="",
            description="test",
        )
        assert parsed.is_valid() is False
