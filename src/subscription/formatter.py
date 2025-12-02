"""Subscription Formatter for display formatting."""
from datetime import date, datetime
from typing import Optional


class SubscriptionFormatter:
    """Format subscription data for display."""
    
    # Emoji progress bar characters
    PROGRESS_FULL = "█"
    PROGRESS_EMPTY = "░"
    PROGRESS_LENGTH = 10
    
    # Warning thresholds
    WARNING_DAYS = 7
    CRITICAL_DAYS = 3
    
    @staticmethod
    def format_countdown(days: int) -> str:
        """Format days remaining with emoji indicators.
        
        Args:
            days: Number of days remaining
            
        Returns:
            Formatted countdown string with appropriate emoji
        """
        if days < 0:
            return "❌ Sudah berakhir"
        elif days == 0:
            return "🔴 Berakhir hari ini!"
        elif days == 1:
            return "🔴 1 hari lagi!"
        elif days <= 3:
            return f"🔴 {days} hari lagi!"
        elif days <= 7:
            return f"⚠️ {days} hari lagi"
        elif days <= 30:
            return f"📆 {days} hari lagi"
        elif days <= 60:
            months = days // 30
            remaining_days = days % 30
            if remaining_days > 0:
                return f"📅 ~{months} bulan {remaining_days} hari"
            return f"📅 ~{months} bulan"
        else:
            months = days // 30
            return f"📅 ~{months} bulan"
    
    @staticmethod
    def format_progress_emoji(progress: float) -> str:
        """Generate emoji progress bar.
        
        Args:
            progress: Progress percentage (0-100)
            
        Returns:
            Emoji progress bar string
        """
        # Clamp progress between 0 and 100
        progress = max(0, min(100, progress))
        
        filled = int(progress / 100 * SubscriptionFormatter.PROGRESS_LENGTH)
        empty = SubscriptionFormatter.PROGRESS_LENGTH - filled
        
        bar = SubscriptionFormatter.PROGRESS_FULL * filled + SubscriptionFormatter.PROGRESS_EMPTY * empty
        
        # Add color indicator based on progress
        if progress >= 90:
            return f"🔴 {bar}"
        elif progress >= 75:
            return f"🟠 {bar}"
        elif progress >= 50:
            return f"🟡 {bar}"
        else:
            return f"🟢 {bar}"
    
    @staticmethod
    def format_amount(amount: float) -> str:
        """Format currency with proper notation.
        
        Args:
            amount: Numeric amount
            
        Returns:
            Formatted currency string (e.g., "Rp 150.000")
        """
        # Handle negative amounts
        if amount < 0:
            return f"-Rp {abs(amount):,.0f}".replace(",", ".")
        return f"Rp {amount:,.0f}".replace(",", ".")
    
    @staticmethod
    def format_relative_date(target_date: date) -> str:
        """Format date as relative time.
        
        Args:
            target_date: Target date to format
            
        Returns:
            Relative time string (e.g., "3 hari lagi", "kemarin")
        """
        today = date.today()
        delta = (target_date - today).days
        
        if delta < -365:
            years = abs(delta) // 365
            return f"{years} tahun lalu"
        elif delta < -30:
            months = abs(delta) // 30
            return f"{months} bulan lalu"
        elif delta < -7:
            weeks = abs(delta) // 7
            return f"{weeks} minggu lalu"
        elif delta < -1:
            return f"{abs(delta)} hari lalu"
        elif delta == -1:
            return "kemarin"
        elif delta == 0:
            return "hari ini"
        elif delta == 1:
            return "besok"
        elif delta < 7:
            return f"{delta} hari lagi"
        elif delta < 30:
            weeks = delta // 7
            if weeks == 1:
                return "1 minggu lagi"
            return f"{weeks} minggu lagi"
        elif delta < 365:
            months = delta // 30
            if months == 1:
                return "1 bulan lagi"
            return f"{months} bulan lagi"
        else:
            years = delta // 365
            if years == 1:
                return "1 tahun lagi"
            return f"{years} tahun lagi"
    
    @staticmethod
    def format_status_emoji(status: str) -> str:
        """Get emoji for subscription status.
        
        Args:
            status: Subscription status (active, expiring_soon, expired)
            
        Returns:
            Status emoji
        """
        status_emojis = {
            "active": "✅",
            "expiring_soon": "⚠️",
            "expired": "❌",
        }
        return status_emojis.get(status, "📦")
    
    @staticmethod
    def format_category_emoji(category: str) -> str:
        """Get emoji for subscription category.
        
        Args:
            category: Subscription category
            
        Returns:
            Category emoji
        """
        category_emojis = {
            "streaming": "🎬",
            "hosting": "🖥️",
            "domain": "🌐",
            "software": "💿",
            "other": "📦",
        }
        return category_emojis.get(category.lower(), "📦")
    
    @staticmethod
    def format_subscription_card(
        name: str,
        amount: float,
        days_remaining: int,
        progress: float,
        status: str,
        category: str,
        start_date: date,
        end_date: date,
        sub_id: int
    ) -> str:
        """Format a complete subscription card for Telegram display.
        
        Args:
            name: Subscription name
            amount: Monthly amount
            days_remaining: Days until expiry
            progress: Progress percentage
            status: Subscription status
            category: Subscription category
            start_date: Start date
            end_date: End date
            sub_id: Subscription ID
            
        Returns:
            Formatted subscription card string
        """
        status_emoji = SubscriptionFormatter.format_status_emoji(status)
        cat_emoji = SubscriptionFormatter.format_category_emoji(category)
        amount_str = SubscriptionFormatter.format_amount(amount)
        countdown = SubscriptionFormatter.format_countdown(days_remaining)
        progress_bar = SubscriptionFormatter.format_progress_emoji(progress)
        relative = SubscriptionFormatter.format_relative_date(end_date)
        
        lines = [
            f"{status_emoji} *{name}* {cat_emoji}",
            f"   💵 {amount_str}/bulan",
            f"   📅 {start_date.strftime('%d/%m/%y')} → {end_date.strftime('%d/%m/%y')}",
            f"   ⏱️ {countdown} ({relative})",
            f"   {progress_bar}",
            f"   🆔 `{sub_id}`",
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def is_warning(days_remaining: int) -> bool:
        """Check if subscription should show warning.
        
        Args:
            days_remaining: Days until expiry
            
        Returns:
            True if warning should be shown
        """
        return days_remaining <= SubscriptionFormatter.WARNING_DAYS
    
    @staticmethod
    def is_critical(days_remaining: int) -> bool:
        """Check if subscription is in critical state.
        
        Args:
            days_remaining: Days until expiry
            
        Returns:
            True if critical warning should be shown
        """
        return days_remaining <= SubscriptionFormatter.CRITICAL_DAYS
