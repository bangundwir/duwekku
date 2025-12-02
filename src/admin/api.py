import logging
from datetime import date
from pathlib import Path
from typing import Optional, List
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.database.sqlite_db import SQLiteDB
from src.admin.services.user_service import UserService
from src.admin.services.subscription_service import SubscriptionService
from src.admin.services.query_limiter import QueryLimiter
from src.admin.services.auth_service import AuthService

TEMPLATES_DIR = Path(__file__).parent / "templates"

logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    message: str


class UserResponse(BaseModel):
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    registered_at: str
    last_active: str
    is_blocked: bool
    daily_query_limit: int
    monthly_query_limit: int
    daily_queries_used: int
    monthly_queries_used: int
    total_queries: int


class PaginatedUsersResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SetLimitsRequest(BaseModel):
    hourly_limit: int = 5
    daily_limit: int = 10
    monthly_limit: int = 300
    reset_hours: int = 1


class AssignSubscriptionRequest(BaseModel):
    plan_id: int
    duration_days: Optional[int] = None


class CreatePlanRequest(BaseModel):
    name: str
    daily_query_limit: int
    monthly_query_limit: int
    price: float
    duration_days: int
    features: List[str] = []


class PlanResponse(BaseModel):
    id: int
    name: str
    daily_query_limit: int
    monthly_query_limit: int
    price: float
    duration_days: int
    features: List[str]
    is_active: bool


class StatsResponse(BaseModel):
    total_users: int
    active_users: int
    blocked_users: int
    active_subscriptions: int
    today_queries: int
    total_transactions: int


class UsageResponse(BaseModel):
    hourly_used: int
    hourly_limit: int
    hourly_remaining: int
    daily_used: int
    daily_limit: int
    daily_remaining: int
    monthly_used: int
    monthly_limit: int
    monthly_remaining: int
    total_queries: int


# ==================== API Application ====================

def create_admin_api(
    db: SQLiteDB,
    admin_username: str,
    admin_password: str,
) -> FastAPI:
    """Create and configure the admin API application."""
    
    app = FastAPI(
        title="Admin Dashboard API",
        description="API for managing Telegram Money Tracker Bot users",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services
    user_service = UserService(db)
    subscription_service = SubscriptionService(db)
    query_limiter = QueryLimiter(db)
    auth_service = AuthService(db, admin_username, admin_password)
    
    # ==================== Auth Middleware ====================
    
    async def get_current_admin(authorization: Optional[str] = Header(None)):
        """Validate session token from Authorization header."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        # Extract token from "Bearer <token>" format
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization format")
        
        token = parts[1]
        session = auth_service.validate_session(token)
        
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        return session
    
    # ==================== Auth Endpoints ====================
    
    @app.post("/api/admin/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Authenticate admin and get session token."""
        token = auth_service.login(request.username, request.password)
        
        if not token:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        return LoginResponse(
            token=token,
            username=request.username,
            message="Login successful",
        )
    
    @app.post("/api/admin/logout")
    async def logout(session=Depends(get_current_admin)):
        """Logout and invalidate session."""
        auth_service.logout(session.token)
        return {"message": "Logged out successfully"}
    
    @app.get("/api/admin/session")
    async def check_session(session=Depends(get_current_admin)):
        """Check if current session is valid."""
        return {
            "valid": True,
            "username": session.admin_username,
            "expires_at": session.expires_at.isoformat(),
        }
    
    # ==================== User Endpoints ====================
    
    @app.get("/api/admin/users", response_model=PaginatedUsersResponse)
    async def get_users(
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        session=Depends(get_current_admin),
    ):
        """Get paginated list of users."""
        result = user_service.get_users(page, per_page, search)
        
        return PaginatedUsersResponse(
            items=[
                UserResponse(
                    user_id=u.user_id,
                    username=u.username,
                    first_name=u.first_name,
                    registered_at=u.registered_at.isoformat(),
                    last_active=u.last_active.isoformat(),
                    is_blocked=u.is_blocked,
                    daily_query_limit=u.daily_query_limit,
                    monthly_query_limit=u.monthly_query_limit,
                    daily_queries_used=u.daily_queries_used,
                    monthly_queries_used=u.monthly_queries_used,
                    total_queries=u.total_queries,
                )
                for u in result.items
            ],
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            total_pages=result.total_pages,
        )
    
    @app.get("/api/admin/users/{user_id}")
    async def get_user(user_id: int, session=Depends(get_current_admin)):
        """Get user details."""
        user = user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get subscription info
        subscription = subscription_service.get_user_subscription(user_id)
        
        return {
            "user": UserResponse(
                user_id=user.user_id,
                username=user.username,
                first_name=user.first_name,
                registered_at=user.registered_at.isoformat(),
                last_active=user.last_active.isoformat(),
                is_blocked=user.is_blocked,
                daily_query_limit=user.daily_query_limit,
                monthly_query_limit=user.monthly_query_limit,
                daily_queries_used=user.daily_queries_used,
                monthly_queries_used=user.monthly_queries_used,
                total_queries=user.total_queries,
            ),
            "subscription": {
                "id": subscription.id,
                "plan_name": subscription.plan_name,
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat(),
                "status": subscription.status,
                "days_remaining": subscription.days_remaining,
            } if subscription else None,
        }
    
    @app.put("/api/admin/users/{user_id}/block")
    async def block_user(user_id: int, session=Depends(get_current_admin)):
        """Block a user."""
        user = user_service.block_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": f"User {user_id} blocked", "is_blocked": True}
    
    @app.put("/api/admin/users/{user_id}/unblock")
    async def unblock_user(user_id: int, session=Depends(get_current_admin)):
        """Unblock a user."""
        user = user_service.unblock_user(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": f"User {user_id} unblocked", "is_blocked": False}
    
    @app.delete("/api/admin/users/{user_id}")
    async def delete_user(user_id: int, session=Depends(get_current_admin)):
        """Delete a user and all related data."""
        if not user_service.delete_user(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": f"User {user_id} deleted"}
    
    @app.post("/api/admin/users/{user_id}/reset")
    async def reset_user_data(user_id: int, session=Depends(get_current_admin)):
        """Reset user data (delete all transactions and subscriptions but keep account)."""
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = user_service.reset_user_data(user_id)
        
        return {
            "message": f"User {user_id} data reset successfully",
            "deleted": result,
        }
    
    # ==================== Query Limit Endpoints ====================
    
    @app.put("/api/admin/users/{user_id}/limits")
    async def set_user_limits(
        user_id: int,
        request: SetLimitsRequest,
        session=Depends(get_current_admin),
    ):
        """Set user's query limits."""
        if not query_limiter.set_limits(
            user_id, 
            request.hourly_limit, 
            request.daily_limit, 
            request.monthly_limit,
            request.reset_hours
        ):
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "message": "Limits updated",
            "hourly_limit": request.hourly_limit,
            "daily_limit": request.daily_limit,
            "monthly_limit": request.monthly_limit,
            "reset_hours": request.reset_hours,
        }
    
    @app.get("/api/admin/users/{user_id}/usage", response_model=UsageResponse)
    async def get_user_usage(user_id: int, session=Depends(get_current_admin)):
        """Get user's usage statistics."""
        usage = query_limiter.get_usage(user_id)
        return UsageResponse(**usage)
    
    # ==================== Subscription Endpoints ====================
    
    @app.get("/api/admin/plans")
    async def get_plans(session=Depends(get_current_admin)):
        """Get all subscription plans."""
        plans = subscription_service.get_plans(active_only=False)
        
        return [
            PlanResponse(
                id=p.id,
                name=p.name,
                daily_query_limit=p.daily_query_limit,
                monthly_query_limit=p.monthly_query_limit,
                price=p.price,
                duration_days=p.duration_days,
                features=p.features,
                is_active=p.is_active,
            )
            for p in plans
        ]
    
    @app.post("/api/admin/plans")
    async def create_plan(request: CreatePlanRequest, session=Depends(get_current_admin)):
        """Create a new subscription plan."""
        plan = subscription_service.create_plan(
            name=request.name,
            daily_query_limit=request.daily_query_limit,
            monthly_query_limit=request.monthly_query_limit,
            price=request.price,
            duration_days=request.duration_days,
            features=request.features,
        )
        
        return PlanResponse(
            id=plan.id,
            name=plan.name,
            daily_query_limit=plan.daily_query_limit,
            monthly_query_limit=plan.monthly_query_limit,
            price=plan.price,
            duration_days=plan.duration_days,
            features=plan.features,
            is_active=plan.is_active,
        )
    
    @app.put("/api/admin/plans/{plan_id}")
    async def update_plan(plan_id: int, request: CreatePlanRequest, session=Depends(get_current_admin)):
        """Update a subscription plan."""
        import json
        if not subscription_service.update_plan(
            plan_id,
            name=request.name,
            daily_query_limit=request.daily_query_limit,
            monthly_query_limit=request.monthly_query_limit,
            price=request.price,
            duration_days=request.duration_days,
            features=json.dumps(request.features),
        ):
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return {"message": f"Plan {plan_id} updated"}
    
    @app.delete("/api/admin/plans/{plan_id}")
    async def delete_plan(plan_id: int, session=Depends(get_current_admin)):
        """Delete a subscription plan."""
        if not subscription_service.delete_plan(plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return {"message": f"Plan {plan_id} deleted"}
    
    @app.put("/api/admin/users/{user_id}/subscription")
    async def assign_subscription(
        user_id: int,
        request: AssignSubscriptionRequest,
        session=Depends(get_current_admin),
    ):
        """Assign a subscription plan to a user."""
        subscription = subscription_service.assign_subscription(
            user_id=user_id,
            plan_id=request.plan_id,
            duration_days=request.duration_days,
            assigned_by=session.admin_username,
        )
        
        if not subscription:
            raise HTTPException(status_code=400, detail="Failed to assign subscription")
        
        return {
            "message": "Subscription assigned",
            "subscription": {
                "id": subscription.id,
                "plan_name": subscription.plan_name,
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat(),
                "status": subscription.status,
            },
        }
    
    # ==================== Analytics Endpoints ====================
    
    @app.get("/api/admin/stats", response_model=StatsResponse)
    async def get_stats(session=Depends(get_current_admin)):
        """Get dashboard statistics."""
        stats = db.get_dashboard_stats()
        return StatsResponse(**stats)
    
    @app.get("/api/admin/analytics/queries")
    async def get_query_analytics(days: int = 30, session=Depends(get_current_admin)):
        """Get daily query volume for the past N days."""
        data = db.get_daily_query_stats(days)
        return {"data": data, "days": days}
    
    # ==================== Frontend Routes ====================
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_page():
        """Serve the admin dashboard HTML."""
        html_file = TEMPLATES_DIR / "index.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)
    
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page():
        """Redirect to dashboard."""
        return await dashboard_page()
    
    return app
