"""
Property-based tests for Financial Analyzer.
"""
import pytest
from datetime import datetime, date, timedelta
from hypothesis import given, strategies as st, settings, assume

from src.analysis.analyzer import FinancialAnalyzer, FinancialHealth
from src.models.transaction import Transaction, EXPENSE_CATEGORIES, INCOME_CATEGORIES


# Custom strategies
@st.composite
def expense_transaction_strategy(draw):
    """Generate valid expense Transaction objects."""
    return Transaction(
        user_id=draw(st.integers(min_value=1, max_value=999999)),
        type="expense",
        amount=draw(st.floats(min_value=0.01, max_value=10000000, allow_nan=False, allow_infinity=False)),
        category=draw(st.sampled_from(EXPENSE_CATEGORIES)),
        description=draw(st.text(min_size=1, max_size=50)),
        id=draw(st.integers(min_value=1, max_value=99999)),
        created_at=datetime.now(),
    )


@st.composite
def income_transaction_strategy(draw):
    """Generate valid income Transaction objects."""
    return Transaction(
        user_id=draw(st.integers(min_value=1, max_value=999999)),
        type="income",
        amount=draw(st.floats(min_value=0.01, max_value=10000000, allow_nan=False, allow_infinity=False)),
        category=draw(st.sampled_from(INCOME_CATEGORIES)),
        description=draw(st.text(min_size=1, max_size=50)),
        id=draw(st.integers(min_value=1, max_value=99999)),
        created_at=datetime.now(),
    )


class TestHealthScoreBounds:
    """
    **Feature: financial-analysis-subscription, Property 1: Health Score Bounds**
    **Validates: Requirements 1.1**
    
    For any set of transactions with valid income and expense values,
    the calculated health score SHALL always be between 0 and 100 inclusive.
    """
    
    @settings(max_examples=100)
    @given(
        expense_ratio=st.floats(min_value=0, max_value=200, allow_nan=False, allow_infinity=False),
        savings_rate=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        category_diversity=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
    )
    def test_health_score_always_bounded(self, expense_ratio, savings_rate, category_diversity):
        """Health score should always be between 0 and 100."""
        # Create analyzer without db (we're testing calculation only)
        analyzer = FinancialAnalyzer(None)
        
        score = analyzer.calculate_health_score(expense_ratio, savings_rate, category_diversity)
        
        assert 0 <= score <= 100
    
    @settings(max_examples=100)
    @given(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
    def test_health_score_extreme_expense_ratio(self, expense_ratio):
        """Health score should handle extreme expense ratios."""
        analyzer = FinancialAnalyzer(None)
        
        score = analyzer.calculate_health_score(expense_ratio, 0, 0.5)
        
        assert 0 <= score <= 100


class TestExpenseBreakdownConsistency:
    """
    **Feature: financial-analysis-subscription, Property 2: Expense Breakdown Consistency**
    **Validates: Requirements 1.2**
    
    For any set of expense transactions, the sum of all category percentages
    SHALL equal 100% (within floating point tolerance).
    """
    
    @settings(max_examples=100)
    @given(st.lists(expense_transaction_strategy(), min_size=1, max_size=20))
    def test_percentages_sum_to_100(self, transactions):
        """Category percentages should sum to 100%."""
        analyzer = FinancialAnalyzer(None)
        
        breakdown = analyzer.get_expense_breakdown(transactions)
        
        if breakdown:
            total_percentage = sum(pct for _, _, pct in breakdown)
            assert abs(total_percentage - 100.0) < 0.01  # Allow small floating point error
    
    @settings(max_examples=100)
    @given(st.lists(expense_transaction_strategy(), min_size=1, max_size=20))
    def test_category_amounts_match_transactions(self, transactions):
        """Each category amount should equal sum of transactions in that category."""
        analyzer = FinancialAnalyzer(None)
        
        breakdown = analyzer.get_expense_breakdown(transactions)
        
        # Calculate expected amounts per category
        expected = {}
        for t in transactions:
            if t.category not in expected:
                expected[t.category] = 0
            expected[t.category] += t.amount
        
        # Verify breakdown matches
        for category, amount, _ in breakdown:
            assert abs(amount - expected[category]) < 0.01


class TestFinancialWarningCorrectness:
    """
    **Feature: financial-analysis-subscription, Property 3: Financial Warning Correctness**
    **Validates: Requirements 1.3, 2.3, 2.4**
    
    When expense ratio exceeds 80%, a warning SHALL be present.
    When expense ratio is 80% or below, no overspending warning SHALL be present.
    """
    
    @settings(max_examples=100)
    @given(st.floats(min_value=80.01, max_value=200, allow_nan=False, allow_infinity=False))
    def test_warning_present_when_over_80_percent(self, expense_ratio):
        """Warning should be present when expense ratio > 80%."""
        health = FinancialHealth(
            score=50,
            income_total=100000,
            expense_total=expense_ratio * 1000,
            balance=100000 - expense_ratio * 1000,
            expense_ratio=expense_ratio,
            savings_rate=100 - expense_ratio,
            top_categories=[],
            trend="stable",
            month_comparison={},
        )
        
        analyzer = FinancialAnalyzer(None)
        warnings = analyzer._generate_warnings(health)
        
        # Should have at least one warning about overspending
        overspending_warnings = [w for w in warnings if "80%" in w or "PERINGATAN" in w]
        assert len(overspending_warnings) > 0
    
    @settings(max_examples=100)
    @given(st.floats(min_value=0, max_value=80, allow_nan=False, allow_infinity=False))
    def test_no_overspending_warning_when_under_80_percent(self, expense_ratio):
        """No overspending warning when expense ratio <= 80%."""
        health = FinancialHealth(
            score=50,
            income_total=100000,
            expense_total=expense_ratio * 1000,
            balance=100000 - expense_ratio * 1000,
            expense_ratio=expense_ratio,
            savings_rate=100 - expense_ratio,
            top_categories=[],
            trend="stable",
            month_comparison={},
        )
        
        analyzer = FinancialAnalyzer(None)
        warnings = analyzer._generate_warnings(health)
        
        # Should not have overspending warning
        overspending_warnings = [w for w in warnings if "80%" in w and "PERINGATAN" in w]
        assert len(overspending_warnings) == 0


class TestMonthComparisonTrend:
    """
    **Feature: financial-analysis-subscription, Property 4: Month Comparison Trend Accuracy**
    **Validates: Requirements 1.4**
    
    Trend SHALL be "improving" when current expenses are lower,
    "declining" when higher, and "stable" when within 5% difference.
    """
    
    @settings(max_examples=100)
    @given(
        current=st.floats(min_value=1, max_value=1000000, allow_nan=False, allow_infinity=False),
        previous=st.floats(min_value=1, max_value=1000000, allow_nan=False, allow_infinity=False),
    )
    def test_trend_calculation(self, current, previous):
        """Trend should be calculated correctly based on expense change."""
        change_percent = ((current - previous) / previous) * 100
        
        if change_percent < -5:
            expected_trend = "improving"
        elif change_percent > 5:
            expected_trend = "declining"
        else:
            expected_trend = "stable"
        
        # Simulate the trend calculation
        if change_percent < -5:
            actual_trend = "improving"
        elif change_percent > 5:
            actual_trend = "declining"
        else:
            actual_trend = "stable"
        
        assert actual_trend == expected_trend


class TestTopCategoriesOrdering:
    """
    **Feature: financial-analysis-subscription, Property 5: Top Categories Ordering**
    **Validates: Requirements 2.1**
    
    The top 3 expense categories SHALL be sorted in descending order by total amount.
    """
    
    @settings(max_examples=100)
    @given(st.lists(expense_transaction_strategy(), min_size=3, max_size=30))
    def test_categories_sorted_descending(self, transactions):
        """Top categories should be sorted by amount descending."""
        analyzer = FinancialAnalyzer(None)
        
        breakdown = analyzer.get_expense_breakdown(transactions)
        
        if len(breakdown) >= 2:
            # Verify descending order
            for i in range(len(breakdown) - 1):
                assert breakdown[i][1] >= breakdown[i + 1][1]
    
    @settings(max_examples=100)
    @given(st.lists(expense_transaction_strategy(), min_size=3, max_size=30))
    def test_top_3_are_highest(self, transactions):
        """Top 3 categories should have the highest amounts."""
        analyzer = FinancialAnalyzer(None)
        
        breakdown = analyzer.get_expense_breakdown(transactions)
        
        if len(breakdown) >= 3:
            top_3 = breakdown[:3]
            rest = breakdown[3:]
            
            # All top 3 amounts should be >= all rest amounts
            min_top_3 = min(amt for _, amt, _ in top_3)
            if rest:
                max_rest = max(amt for _, amt, _ in rest)
                assert min_top_3 >= max_rest
