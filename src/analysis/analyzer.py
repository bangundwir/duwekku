"""Financial Analyzer for calculating financial health and generating suggestions."""
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.models.transaction import Transaction

logger = logging.getLogger(__name__)


@dataclass
class FinancialHealth:
    """Data class representing financial health analysis results."""
    score: int                    # 0-100
    income_total: float
    expense_total: float
    balance: float
    expense_ratio: float          # expense/income percentage (0-100+)
    savings_rate: float           # savings/income percentage
    top_categories: list[tuple[str, float, float]]  # (category, amount, percentage)
    trend: str                    # "improving", "stable", "declining"
    month_comparison: dict        # current vs previous month
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    # Subscription info
    subscription_count: int = 0
    subscription_monthly_cost: float = 0.0
    expiring_subscriptions: list = field(default_factory=list)


class FinancialAnalyzer:
    """Analyzer for calculating financial health metrics."""
    
    def __init__(self, db_manager, subscription_manager=None):
        """Initialize with database manager and optional subscription manager."""
        self.db = db_manager
        self.subscription_manager = subscription_manager
    
    def analyze(self, user_id: int, month: Optional[int] = None, year: Optional[int] = None) -> Optional[FinancialHealth]:
        """Perform comprehensive financial analysis."""
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        
        # Get transactions for current month
        transactions = self.db.get_transactions_by_month(user_id, month, year)
        
        # Check minimum data requirement
        if len(transactions) < 5:
            return None  # Insufficient data
        
        # Calculate totals
        income_total = sum(t.amount for t in transactions if t.type == "income")
        expense_total = sum(t.amount for t in transactions if t.type == "expense")
        balance = income_total - expense_total
        
        # Calculate ratios
        expense_ratio = (expense_total / income_total * 100) if income_total > 0 else 100
        savings_rate = ((income_total - expense_total) / income_total * 100) if income_total > 0 else 0
        
        # Get expense breakdown
        expense_transactions = [t for t in transactions if t.type == "expense"]
        top_categories = self.get_expense_breakdown(expense_transactions)
        
        # Calculate category diversity for health score
        category_diversity = self._calculate_category_diversity(top_categories)
        
        # Calculate health score
        score = self.calculate_health_score(expense_ratio, savings_rate, category_diversity)
        
        # Compare with previous month
        month_comparison = self.compare_months(user_id, month, year)
        trend = month_comparison.get("trend", "stable")
        
        # Get subscription info if available
        subscription_count = 0
        subscription_monthly_cost = 0.0
        expiring_subscriptions = []
        
        if self.subscription_manager:
            try:
                active_subs = self.subscription_manager.get_subscriptions(user_id, include_expired=False)
                subscription_count = len(active_subs)
                subscription_monthly_cost = sum(s.amount for s in active_subs)
                expiring_subscriptions = self.subscription_manager.get_expiring_soon(user_id, days=7)
            except Exception as e:
                logger.warning(f"Failed to get subscription info: {e}")
        
        # Create health object
        health = FinancialHealth(
            score=score,
            income_total=income_total,
            expense_total=expense_total,
            balance=balance,
            expense_ratio=expense_ratio,
            savings_rate=savings_rate,
            top_categories=top_categories,
            trend=trend,
            month_comparison=month_comparison,
            subscription_count=subscription_count,
            subscription_monthly_cost=subscription_monthly_cost,
            expiring_subscriptions=expiring_subscriptions,
        )
        
        # Generate warnings and suggestions
        health.warnings = self._generate_warnings(health)
        health.suggestions = self.generate_suggestions(health)
        
        return health
    
    def calculate_health_score(self, expense_ratio: float, savings_rate: float, 
                                category_diversity: float) -> int:
        """
        Calculate health score 0-100 based on multiple factors.
        
        Components:
        - Expense Ratio Score (40%): Lower is better
        - Savings Rate Score (40%): Higher is better
        - Category Diversity Score (20%): More diverse is better
        """
        # Expense Ratio Score (40 points max)
        if expense_ratio < 50:
            expense_score = 40
        elif expense_ratio < 70:
            expense_score = 30
        elif expense_ratio < 80:
            expense_score = 20
        elif expense_ratio < 90:
            expense_score = 10
        else:
            expense_score = 0
        
        # Savings Rate Score (40 points max)
        if savings_rate > 30:
            savings_score = 40
        elif savings_rate > 20:
            savings_score = 30
        elif savings_rate > 10:
            savings_score = 20
        elif savings_rate > 0:
            savings_score = 10
        else:
            savings_score = 0
        
        # Category Diversity Score (20 points max)
        # category_diversity is 0-1, multiply by 20
        diversity_score = int(category_diversity * 20)
        
        total = expense_score + savings_score + diversity_score
        return max(0, min(100, total))
    
    def get_expense_breakdown(self, transactions: list[Transaction]) -> list[tuple[str, float, float]]:
        """Get expense breakdown by category with amounts and percentages."""
        if not transactions:
            return []
        
        # Sum by category
        category_totals = {}
        for t in transactions:
            if t.category not in category_totals:
                category_totals[t.category] = 0
            category_totals[t.category] += t.amount
        
        total_expense = sum(category_totals.values())
        if total_expense == 0:
            return []
        
        # Calculate percentages and sort by amount descending
        breakdown = []
        for category, amount in category_totals.items():
            percentage = (amount / total_expense) * 100
            breakdown.append((category, amount, percentage))
        
        # Sort by amount descending
        breakdown.sort(key=lambda x: x[1], reverse=True)
        
        return breakdown
    
    def compare_months(self, user_id: int, current_month: int, current_year: int) -> dict:
        """Compare current month with previous month."""
        # Calculate previous month
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
        
        # Get summaries
        current_summary = self.db.get_summary(user_id, current_month, current_year)
        prev_summary = self.db.get_summary(user_id, prev_month, prev_year)
        
        current_expense = current_summary["expense"]
        prev_expense = prev_summary["expense"]
        
        # Calculate trend
        if prev_expense == 0:
            trend = "stable"
            change_percent = 0
        else:
            change_percent = ((current_expense - prev_expense) / prev_expense) * 100
            
            if change_percent < -5:
                trend = "improving"
            elif change_percent > 5:
                trend = "declining"
            else:
                trend = "stable"
        
        return {
            "current_expense": current_expense,
            "previous_expense": prev_expense,
            "change_percent": change_percent,
            "trend": trend,
            "current_month": current_month,
            "previous_month": prev_month,
        }
    
    def generate_suggestions(self, health: FinancialHealth) -> list[str]:
        """Generate personalized financial suggestions."""
        suggestions = []
        
        # Identify top 3 categories and suggest reduction
        if health.top_categories:
            top_3 = health.top_categories[:3]
            for category, amount, percentage in top_3:
                amount_str = f"{amount:,.0f}".replace(",", ".")
                if percentage > 30:
                    suggestions.append(
                        f"💡 Kategori '{category}' menggunakan {percentage:.1f}% dari pengeluaran "
                        f"(Rp {amount_str}). Pertimbangkan untuk mengurangi pengeluaran di kategori ini."
                    )
        
        # Positive savings suggestion
        if health.balance > 0:
            balance_str = f"{health.balance:,.0f}".replace(",", ".")
            suggestions.append(
                f"🎉 Selamat! Anda memiliki saldo positif Rp {balance_str}. "
                "Pertimbangkan untuk menabung atau berinvestasi."
            )
        
        # Negative balance tips
        if health.balance < 0:
            suggestions.append(
                "📉 Pengeluaran melebihi pemasukan. Tips untuk mengurangi pengeluaran:\n"
                "• Buat anggaran bulanan dan patuhi\n"
                "• Kurangi pengeluaran tidak penting\n"
                "• Cari sumber pendapatan tambahan"
            )
        
        # Trend-based suggestions
        if health.trend == "improving":
            suggestions.append("📈 Trend pengeluaran membaik! Pertahankan kebiasaan baik ini.")
        elif health.trend == "declining":
            suggestions.append("📉 Pengeluaran meningkat dari bulan lalu. Perhatikan pola pengeluaran Anda.")
        
        return suggestions
    
    def _generate_warnings(self, health: FinancialHealth) -> list[str]:
        """Generate warning messages based on financial health."""
        warnings = []
        
        # Overspending warning
        if health.expense_ratio > 80:
            warnings.append(
                f"⚠️ PERINGATAN: Rasio pengeluaran Anda {health.expense_ratio:.1f}% dari pemasukan. "
                "Ini melebihi batas aman 80%!"
            )
        
        # High spending category warning
        for category, amount, percentage in health.top_categories:
            if percentage > 30:
                warnings.append(
                    f"⚠️ Kategori '{category}' menyumbang {percentage:.1f}% dari total pengeluaran."
                )
        
        return warnings
    
    def _calculate_category_diversity(self, breakdown: list[tuple[str, float, float]]) -> float:
        """
        Calculate category diversity using entropy-based calculation.
        Returns value between 0 (all in one category) and 1 (evenly distributed).
        """
        if not breakdown or len(breakdown) <= 1:
            return 0.0
        
        # Calculate entropy
        entropy = 0.0
        for _, _, percentage in breakdown:
            if percentage > 0:
                p = percentage / 100
                entropy -= p * math.log2(p)
        
        # Normalize by max entropy (log2 of number of categories)
        max_entropy = math.log2(len(breakdown))
        if max_entropy == 0:
            return 0.0
        
        return entropy / max_entropy
