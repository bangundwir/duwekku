"""Subscription Manager for handling subscription CRUD operations."""
import logging
from datetime import date
from typing import Optional

from src.models.subscription import Subscription, SUBSCRIPTION_CATEGORIES

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """Manager class for subscription operations."""
    
    def __init__(self, db_manager):
        """Initialize with database manager."""
        self.db = db_manager
    
    def add_subscription(self, subscription: Subscription) -> int:
        """Add new subscription, return ID."""
        # Validate category
        if subscription.category not in SUBSCRIPTION_CATEGORIES:
            subscription.category = "other"
        
        # Insert to local DB
        sub_id = self.db.sqlite.insert_subscription(subscription)
        subscription.id = sub_id
        
        # Sync to cloud if available
        if self.db.tidb:
            try:
                self.db.tidb.insert_subscription(subscription)
                self.db.sqlite.mark_subscription_synced(sub_id)
            except Exception as e:
                logger.warning(f"Failed to sync subscription to cloud: {e}")
        
        return sub_id
    
    def get_subscriptions(self, user_id: int, include_expired: bool = False) -> list[Subscription]:
        """Get all subscriptions for user."""
        return self.db.sqlite.get_subscriptions(user_id, include_expired)
    
    def get_subscription_by_id(self, user_id: int, sub_id: int) -> Optional[Subscription]:
        """Get specific subscription by ID."""
        return self.db.sqlite.get_subscription_by_id(user_id, sub_id)
    
    def delete_subscription(self, user_id: int, sub_id: int) -> bool:
        """Delete subscription. Returns True if deleted."""
        result = self.db.sqlite.delete_subscription(user_id, sub_id)
        
        if result and self.db.tidb:
            try:
                self.db.tidb.delete_subscription(sub_id)
            except Exception as e:
                logger.warning(f"Failed to delete subscription from cloud: {e}")
        
        return result
    
    def renew_subscription(self, user_id: int, sub_id: int, new_end_date: date) -> bool:
        """Update subscription end date for renewal."""
        result = self.db.sqlite.update_subscription_end_date(user_id, sub_id, new_end_date)
        
        if result and self.db.tidb:
            try:
                sub = self.db.sqlite.get_subscription_by_id(user_id, sub_id)
                if sub:
                    self.db.tidb.insert_subscription(sub)
            except Exception as e:
                logger.warning(f"Failed to sync renewed subscription to cloud: {e}")
        
        return result
    
    def get_expiring_soon(self, user_id: int, days: int = 7) -> list[Subscription]:
        """Get subscriptions expiring within specified days."""
        return self.db.sqlite.get_expiring_subscriptions(user_id, days)
    
    def get_monthly_cost(self, user_id: int) -> dict:
        """Calculate total monthly subscription cost with breakdown by category."""
        subscriptions = self.get_subscriptions(user_id, include_expired=False)
        
        total = 0.0
        by_category = {}
        
        for sub in subscriptions:
            total += sub.amount
            if sub.category not in by_category:
                by_category[sub.category] = 0.0
            by_category[sub.category] += sub.amount
        
        return {
            "total": total,
            "by_category": by_category,
            "count": len(subscriptions),
        }
    
    def get_by_category(self, user_id: int) -> dict[str, list[Subscription]]:
        """Group subscriptions by category."""
        subscriptions = self.get_subscriptions(user_id, include_expired=True)
        
        grouped = {}
        for sub in subscriptions:
            if sub.category not in grouped:
                grouped[sub.category] = []
            grouped[sub.category].append(sub)
        
        return grouped
