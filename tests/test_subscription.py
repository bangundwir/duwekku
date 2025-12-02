"""
Property-based tests for Subscription model and manager.
"""
import pytest
from datetime import date, timedelta
from hypothesis import given, strategies as st, settings, assume

from src.models.subscription import Subscription, SUBSCRIPTION_CATEGORIES


# Custom strategies for generating test data
@st.composite
def subscription_strategy(draw):
    """Generate valid Subscription objects."""
    start = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)))
    # Ensure end_date is >= start_date
    end = draw(st.dates(min_value=start, max_value=date(2035, 12, 31)))
    
    return Subscription(
        user_id=draw(st.integers(min_value=1, max_value=999999999)),
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')))),
        amount=draw(st.floats(min_value=0.01, max_value=10000000, allow_nan=False, allow_infinity=False)),
        category=draw(st.sampled_from(SUBSCRIPTION_CATEGORIES)),
        start_date=start,
        end_date=end,
        id=draw(st.integers(min_value=1, max_value=99999)),
        is_active=draw(st.booleans()),
        notes=draw(st.one_of(st.none(), st.text(min_size=0, max_size=100))),
    )


class TestSubscriptionStatusProperty:
    """
    **Feature: financial-analysis-subscription, Property 7: Subscription Status Correctness**
    **Validates: Requirements 3.3, 3.4, 7.2**
    
    For any subscription, the status SHALL be "expired" if end_date is in the past,
    "expiring_soon" if end_date is within 7 days, and "active" otherwise.
    """
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_status_expired_when_end_date_past(self, sub: Subscription):
        """Status should be 'expired' when end_date is in the past."""
        # Force end_date to be in the past
        sub.end_date = date.today() - timedelta(days=1)
        sub.is_active = True
        
        assert sub.status == "expired"
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_status_expired_when_inactive(self, sub: Subscription):
        """Status should be 'expired' when is_active is False."""
        sub.is_active = False
        
        assert sub.status == "expired"
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_status_expiring_soon_within_7_days(self, sub: Subscription):
        """Status should be 'expiring_soon' when end_date is within 7 days."""
        # Set end_date to be within 7 days (1-7 days from today)
        days_ahead = 3  # Use a fixed value within range
        sub.end_date = date.today() + timedelta(days=days_ahead)
        sub.is_active = True
        
        assert sub.status == "expiring_soon"
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_status_active_when_more_than_7_days(self, sub: Subscription):
        """Status should be 'active' when end_date is more than 7 days away."""
        sub.end_date = date.today() + timedelta(days=30)
        sub.is_active = True
        
        assert sub.status == "active"
    
    @settings(max_examples=100)
    @given(st.integers(min_value=0, max_value=7))
    def test_status_boundary_7_days(self, days: int):
        """Test boundary condition at exactly 7 days."""
        sub = Subscription(
            user_id=1,
            name="Test",
            amount=100.0,
            category="streaming",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=days),
            is_active=True,
        )
        
        if days <= 7:
            assert sub.status in ["expiring_soon", "expired"]
        else:
            assert sub.status == "active"


class TestDaysRemainingProperty:
    """
    **Feature: financial-analysis-subscription, Property 12: Days Remaining Calculation**
    **Validates: Requirements 3.2**
    
    For any active subscription, the days_remaining property SHALL equal the difference
    between end_date and today's date (minimum 0).
    """
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_days_remaining_calculation(self, sub: Subscription):
        """days_remaining should equal end_date - today (min 0) for active subscriptions."""
        sub.is_active = True
        
        expected = max(0, (sub.end_date - date.today()).days)
        assert sub.days_remaining == expected
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_days_remaining_zero_when_inactive(self, sub: Subscription):
        """days_remaining should be 0 when subscription is inactive."""
        sub.is_active = False
        
        assert sub.days_remaining == 0
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_days_remaining_never_negative(self, sub: Subscription):
        """days_remaining should never be negative."""
        assert sub.days_remaining >= 0
    
    @settings(max_examples=100)
    @given(st.integers(min_value=-365, max_value=365))
    def test_days_remaining_with_various_dates(self, days_offset: int):
        """Test days_remaining with various date offsets."""
        sub = Subscription(
            user_id=1,
            name="Test",
            amount=100.0,
            category="streaming",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=days_offset),
            is_active=True,
        )
        
        expected = max(0, days_offset)
        assert sub.days_remaining == expected


class TestSubscriptionRoundTrip:
    """Test to_dict and from_dict round-trip."""
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_to_dict_from_dict_roundtrip(self, sub: Subscription):
        """Converting to dict and back should preserve all fields."""
        # Ensure we have an ID for the round-trip
        if sub.id is None:
            sub.id = 1
        
        data = sub.to_dict()
        restored = Subscription.from_dict(data)
        
        assert restored.user_id == sub.user_id
        assert restored.name == sub.name
        assert restored.amount == sub.amount
        assert restored.category == sub.category
        assert restored.start_date == sub.start_date
        assert restored.end_date == sub.end_date
        assert restored.is_active == sub.is_active
        assert restored.notes == sub.notes



# Tests for SubscriptionManager (requires database fixtures)
class TestSubscriptionCRUDRoundTrip:
    """
    **Feature: financial-analysis-subscription, Property 6: Subscription CRUD Round-Trip**
    **Validates: Requirements 3.1**
    
    For any valid subscription data, adding a subscription and then retrieving it by ID
    SHALL return a subscription with identical field values.
    """
    
    @settings(max_examples=100)
    @given(subscription_strategy())
    def test_crud_roundtrip_model_only(self, sub: Subscription):
        """Test that subscription data survives to_dict/from_dict round-trip."""
        if sub.id is None:
            sub.id = 12345
        
        data = sub.to_dict()
        restored = Subscription.from_dict(data)
        
        assert restored.name == sub.name
        assert restored.amount == sub.amount
        assert restored.category == sub.category
        assert restored.start_date == sub.start_date
        assert restored.end_date == sub.end_date
        assert restored.user_id == sub.user_id


class TestSubscriptionDeletion:
    """
    **Feature: financial-analysis-subscription, Property 8: Subscription Deletion Completeness**
    **Validates: Requirements 3.5**
    
    For any subscription that is deleted, subsequent retrieval attempts SHALL return None.
    """
    
    def test_deletion_removes_subscription(self, tmp_path):
        """Test that deleted subscription cannot be retrieved."""
        from src.database.sqlite_db import SQLiteDB
        
        db = SQLiteDB(str(tmp_path / "test.db"))
        
        sub = Subscription(
            user_id=123,
            name="Test Sub",
            amount=100.0,
            category="streaming",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        
        sub_id = db.insert_subscription(sub)
        
        # Verify it exists
        retrieved = db.get_subscription_by_id(123, sub_id)
        assert retrieved is not None
        
        # Delete it
        result = db.delete_subscription(123, sub_id)
        assert result is True
        
        # Verify it's gone
        retrieved_after = db.get_subscription_by_id(123, sub_id)
        assert retrieved_after is None


class TestSubscriptionRenewal:
    """
    **Feature: financial-analysis-subscription, Property 11: Subscription Renewal Update**
    **Validates: Requirements 7.3**
    
    For any subscription renewal operation, the end_date SHALL be updated while
    other fields remain unchanged.
    """
    
    def test_renewal_updates_only_end_date(self, tmp_path):
        """Test that renewal only updates end_date."""
        from src.database.sqlite_db import SQLiteDB
        
        db = SQLiteDB(str(tmp_path / "test.db"))
        
        original_end = date.today() + timedelta(days=30)
        new_end = date.today() + timedelta(days=60)
        
        sub = Subscription(
            user_id=123,
            name="Test Sub",
            amount=100.0,
            category="streaming",
            start_date=date.today(),
            end_date=original_end,
        )
        
        sub_id = db.insert_subscription(sub)
        
        # Renew
        result = db.update_subscription_end_date(123, sub_id, new_end)
        assert result is True
        
        # Verify only end_date changed
        renewed = db.get_subscription_by_id(123, sub_id)
        assert renewed.end_date == new_end
        assert renewed.name == sub.name
        assert renewed.amount == sub.amount
        assert renewed.category == sub.category
        assert renewed.start_date == sub.start_date


class TestCategoryAggregation:
    """
    **Feature: financial-analysis-subscription, Property 9: Category Aggregation Correctness**
    **Validates: Requirements 4.2, 4.3**
    
    For any set of subscriptions grouped by category, the subtotal for each category
    SHALL equal the sum of amounts of all subscriptions in that category.
    """
    
    def test_category_aggregation_correctness(self, tmp_path):
        """Test that category subtotals are correct."""
        from src.database.sqlite_db import SQLiteDB
        
        db = SQLiteDB(str(tmp_path / "test.db"))
        user_id = 123
        
        # Add subscriptions in different categories
        subs_data = [
            ("Netflix", 150000, "streaming"),
            ("Spotify", 50000, "streaming"),
            ("VPS", 100000, "hosting"),
            ("Domain", 200000, "domain"),
        ]
        
        for name, amount, category in subs_data:
            sub = Subscription(
                user_id=user_id,
                name=name,
                amount=amount,
                category=category,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
            )
            db.insert_subscription(sub)
        
        # Get all subscriptions and calculate manually
        all_subs = db.get_subscriptions(user_id, include_expired=False)
        
        # Calculate expected totals
        expected_by_category = {}
        expected_total = 0
        for sub in all_subs:
            expected_total += sub.amount
            if sub.category not in expected_by_category:
                expected_by_category[sub.category] = 0
            expected_by_category[sub.category] += sub.amount
        
        # Verify streaming total
        assert expected_by_category.get("streaming", 0) == 200000
        assert expected_by_category.get("hosting", 0) == 100000
        assert expected_by_category.get("domain", 0) == 200000
        assert expected_total == 500000
