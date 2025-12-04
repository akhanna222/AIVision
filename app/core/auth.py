"""
Authentication and authorization for API access.
Token-based authentication system.
"""

from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import crud
from app.db.models import Account

security = HTTPBearer()


async def get_current_account(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Account:
    """
    Validate API token and return current account.
    Usage: account = Depends(get_current_account)
    """
    token = credentials.credentials

    # Validate token format
    if not token.startswith("aiv_"):
        raise HTTPException(
            status_code=401,
            detail="Invalid API token format"
        )

    # Get account by token
    account = crud.get_account_by_token(db, token)

    if not account:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API token"
        )

    if not account.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    # Check monthly limits
    if account.monthly_extractions >= account.monthly_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly extraction limit ({account.monthly_limit}) exceeded"
        )

    return account


def check_extraction_limit(account: Account) -> bool:
    """Check if account can perform extraction"""
    return account.monthly_extractions < account.monthly_limit


def get_remaining_extractions(account: Account) -> int:
    """Get remaining extractions for the month"""
    return max(0, account.monthly_limit - account.monthly_extractions)


# Plan-based limits
PLAN_LIMITS = {
    "free": {
        "monthly_extractions": 100,
        "max_file_size_mb": 10,
        "enabled_models": ["gemini-2.0-flash-exp"],
        "custom_templates": 3,
        "api_rate_limit": 10  # requests per minute
    },
    "starter": {
        "monthly_extractions": 1000,
        "max_file_size_mb": 25,
        "enabled_models": ["gemini-2.0-flash-exp", "gpt-4o-mini"],
        "custom_templates": 10,
        "api_rate_limit": 30
    },
    "professional": {
        "monthly_extractions": 10000,
        "max_file_size_mb": 50,
        "enabled_models": ["gemini-2.0-flash-exp", "gpt-4o", "claude-sonnet-4-20250514"],
        "custom_templates": 50,
        "api_rate_limit": 100
    },
    "enterprise": {
        "monthly_extractions": -1,  # Unlimited
        "max_file_size_mb": 100,
        "enabled_models": ["gemini-2.0-flash-exp", "gemini-2.5-pro-preview", "gpt-4o", "claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        "custom_templates": -1,  # Unlimited
        "api_rate_limit": -1  # Unlimited
    }
}


def get_plan_limits(plan: str) -> dict:
    """Get limits for a plan"""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def can_use_model(account: Account, model: str) -> bool:
    """Check if account can use specific model"""
    return model in account.enabled_models
