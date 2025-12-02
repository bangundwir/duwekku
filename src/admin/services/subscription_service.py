import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, List

from src.database.sqlite_db import SQLiteDB
from src.models.subscription_plan import SubscriptionPlan, DEFAULT_PLANS
from src.models.user_subscription import UserSubscription

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription management."""
    
    def __init__(self, db: SQLiteDB):
        self.db = db
        self._ensure_default_plans()
    
    def _ensure_default_plans(self) -> None:
        """Ensure default subscription plans exist."""
        existing = self.db.get_all_subscription_plans(active_only=False)
        if not existing:
            logger.info("Creating default subscription plans...")
            for plan in DEFAULT_PLANS:
                self.db.create_subscription_plan(plan)
            logger.info(f"Created {len(DEFAULT_PLANS)} default plans")
    
    def get_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        """Get all subscription plans."""
        return self.db.get_all_subscription_plans(active_only)
    
    def get_plan(self, plan_id: int) -> Optional[SubscriptionPlan]:
        """Get a subscription plan by ID."""
        return self.db.get_subscription_plan(plan_id)
    
    def create_plan(
        self,
        name: str,
        daily_query_limit: int,
        monthly_query_limit: int,
        price: float,
        duration_days: int,
        features: List[str] = None,
    ) -> SubscriptionPlan:
        """Create a new subscription plan."""
        plan = SubscriptionPlan(
            name=name,
            daily_query_limit=daily_query_limit,
            monthly_query_limit=monthly_query_limit,
            price=price,
            duration_days=duration_days,
            features=features or [],
        )
        plan_id = self.db.create_subscription_plan(plan)
        plan.id = plan_id
        return plan
    
    def update_plan(self, plan_id: int, **kwargs) -> bool:
        """Update a subscription plan."""
        return self.db.update_subscription_plan(plan_id, **kwargs)
    
    def assign_subscription(
        self,
        user_id: int,
        plan_id: int,
        duration_days: Optional[int] = None,
        assigned_by: str = "admin",
    ) -> Optional[UserSubscription]:
        """Assign a subscription plan to a user."""
        plan = self.db.get_subscription_plan(plan_id)
        if not plan:
            logger.error(f"Plan {plan_id} not found")
            return None
        
        # Use plan's duration if not specified
        days = duration_days or plan.duration_days
        
        start_date = date.today()
        end_date = start_date + relativedelta(days=days)
        
        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            plan_name=plan.name,
            start_date=start_date,
            end_date=end_date,
            status="active",
            assigned_by=assigned_by,
            assigned_at=datetime.now(),
        )
        
        sub_id = self.db.assign_user_subscription(subscription)
        subscription.id = sub_id
        
        # Update user's query limits based on plan
        self.db.update_bot_user_limits(
            user_id, 
            plan.daily_query_limit, 
            plan.monthly_query_limit
        )
        
        logger.info(f"Assigned plan {plan.name} to user {user_id}")
        return subscription
    
    def get_user_subscription(self, user_id: int) -> Optional[UserSubscription]:
        """Get user's current active subscription."""
        return self.db.get_user_subscription(user_id)
    
    def get_user_subscription_history(self, user_id: int) -> List[UserSubscription]:
        """Get user's subscription history."""
        return self.db.get_user_subscription_history(user_id)
    
    def check_expired_subscriptions(self) -> int:
        """Check and mark expired subscriptions. Returns count of expired."""
        count = self.db.expire_user_subscriptions()
        if count > 0:
            logger.info(f"Marked {count} subscriptions as expired")
        return count
    
    def get_active_subscriptions_count(self) -> int:
        """Get count of active subscriptions."""
        return self.db.get_active_subscriptions_count()
