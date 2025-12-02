# Testing Documentation

Dokumentasi lengkap untuk testing Money Tracker Bot.

## Overview

Project menggunakan pytest untuk unit testing dan hypothesis untuk property-based testing.

## Struktur Test

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures
├── test_analyzer.py      # Financial analyzer tests
├── test_database.py      # Database tests
├── test_models.py        # Model tests
├── test_parser.py        # AI parser tests
└── test_subscription.py  # Subscription tests
```

## Menjalankan Tests

### Semua Tests
```bash
uv run pytest tests/ -v
```

### Test Spesifik
```bash
uv run pytest tests/test_models.py -v
```

### Dengan Coverage
```bash
uv run pytest tests/ --cov=src --cov-report=html
```

## Test Files

### test_models.py
Test untuk data models.

```python
class TestTransaction:
    def test_to_dict()
    def test_from_dict()
    def test_format_display_expense()
    def test_format_display_income()
    def test_format_short()
```

### test_database.py
Test untuk database operations.

```python
class TestSQLiteDB:
    def test_insert_and_get_transaction()
    def test_get_transaction_by_id()
    def test_delete_transaction()
    def test_delete_nonexistent()
    def test_get_summary()
    def test_mark_synced()
    def test_transactions_ordered_by_newest()

class TestDatabaseManager:
    def test_save_transaction()
    def test_get_transactions()
    def test_delete_transaction()
```

### test_parser.py
Test untuk AI parser.

```python
class TestNormalizeAmount:
    def test_ribu_suffix()      # 50rb → 50000
    def test_juta_suffix()      # 5jt → 5000000
    def test_k_suffix()         # 50k → 50000
    def test_decimal_amounts()
    def test_plain_numbers()
    def test_invalid_input()

class TestParsedTransaction:
    def test_valid_expense()
    def test_valid_income()
    def test_invalid_type()
    def test_invalid_amount()
    def test_empty_category()
```

### test_subscription.py
Test untuk subscription system.

```python
class TestSubscriptionStatusProperty:
    def test_status_expired_when_end_date_past()
    def test_status_expired_when_inactive()
    def test_status_expiring_soon_within_7_days()
    def test_status_active_when_more_than_7_days()
    def test_status_boundary_7_days()

class TestDaysRemainingProperty:
    def test_days_remaining_calculation()
    def test_days_remaining_zero_when_inactive()
    def test_days_remaining_never_negative()
    def test_days_remaining_with_various_dates()

class TestSubscriptionRoundTrip:
    def test_to_dict_from_dict_roundtrip()

class TestSubscriptionCRUDRoundTrip:
    def test_crud_roundtrip_model_only()

class TestSubscriptionDeletion:
    def test_deletion_removes_subscription()

class TestSubscriptionRenewal:
    def test_renewal_updates_only_end_date()

class TestCategoryAggregation:
    def test_category_aggregation_correctness()
```

### test_analyzer.py
Test untuk financial analyzer.

```python
class TestHealthScoreBounds:
    def test_health_score_always_bounded()
    def test_health_score_extreme_expense_ratio()

class TestExpenseBreakdownConsistency:
    def test_percentages_sum_to_100()
    def test_category_amounts_match_transactions()

class TestFinancialWarningCorrectness:
    def test_warning_present_when_over_80_percent()
    def test_no_overspending_warning_when_under_80_percent()

class TestMonthComparisonTrend:
    def test_trend_calculation()

class TestTopCategoriesOrdering:
    def test_categories_sorted_descending()
    def test_top_3_are_highest()
```

## Fixtures (conftest.py)

### Database Fixtures
```python
@pytest.fixture
def temp_db():
    """Create temporary SQLite database."""
    ...

@pytest.fixture
def db_manager(temp_db):
    """Create DatabaseManager with temp db."""
    ...
```

### Sample Data Fixtures
```python
@pytest.fixture
def sample_transaction():
    """Create sample transaction."""
    ...

@pytest.fixture
def sample_subscription():
    """Create sample subscription."""
    ...
```

## Property-Based Testing

Menggunakan Hypothesis untuk property-based testing.

### Contoh
```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=1000000))
def test_amount_always_positive(amount):
    transaction = Transaction(amount=amount, ...)
    assert transaction.amount >= 0
```

### Strategies
- `st.integers()` - Generate integers
- `st.floats()` - Generate floats
- `st.text()` - Generate strings
- `st.dates()` - Generate dates
- `st.datetimes()` - Generate datetimes

## Best Practices

### 1. Isolasi Test
Setiap test harus independen dan tidak bergantung pada test lain.

### 2. Fixtures
Gunakan fixtures untuk setup yang berulang.

### 3. Naming
Nama test harus deskriptif:
```python
def test_transaction_with_negative_amount_raises_error():
    ...
```

### 4. Assertions
Gunakan assertions yang spesifik:
```python
assert result == expected  # Good
assert result              # Bad (tidak jelas)
```

### 5. Edge Cases
Test edge cases:
- Empty inputs
- Boundary values
- Invalid inputs
- Error conditions

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run tests
  run: |
    uv sync
    uv run pytest tests/ -v --cov=src
```

### Pre-commit Hook
```bash
#!/bin/sh
uv run pytest tests/ -v
```

## Troubleshooting

### Test Gagal
1. Cek error message
2. Jalankan test individual
3. Cek fixtures
4. Cek database state

### Slow Tests
1. Gunakan `pytest -x` untuk stop on first failure
2. Gunakan `pytest -k "keyword"` untuk filter
3. Parallel execution dengan `pytest-xdist`
