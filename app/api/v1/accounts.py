"""
Account management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.db.session import get_db
from app.db import crud
from app.core.auth import get_current_account, get_plan_limits
from app.db.models import Account

router = APIRouter()


# Request/Response models
class AccountCreate(BaseModel):
    name: str
    email: EmailStr
    plan: str = "free"


class AccountResponse(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    is_active: bool
    api_token: str
    total_extractions: int
    monthly_extractions: int
    monthly_limit: int
    default_vision_model: str

    class Config:
        from_attributes = True


class TokenRegenerateResponse(BaseModel):
    api_token: str
    message: str


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db)
):
    """
    Create new account.

    - Generates API token
    - Sets up default countries
    - Initializes usage limits based on plan
    """
    # Check if email already exists
    existing = crud.get_account_by_email(db, account_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Get plan limits
    plan_limits = get_plan_limits(account_data.plan)

    # Create account
    account = crud.create_account(
        db,
        name=account_data.name,
        email=account_data.email,
        plan=account_data.plan
    )

    # Set limits based on plan
    account.monthly_limit = plan_limits["monthly_extractions"]
    db.commit()

    return account


@router.get("/me", response_model=AccountResponse)
async def get_current_account_info(
    account: Account = Depends(get_current_account)
):
    """
    Get current account information.

    Requires authentication token.
    """
    return account


@router.post("/regenerate-token", response_model=TokenRegenerateResponse)
async def regenerate_token(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Regenerate API token.

    **Warning**: Old token will be invalidated immediately.
    """
    new_token = crud.regenerate_api_token(db, account.id)

    return {
        "api_token": new_token,
        "message": "API token regenerated successfully. Update your applications with the new token."
    }


@router.get("/usage")
async def get_account_usage(
    account: Account = Depends(get_current_account)
):
    """
    Get account usage statistics.

    Returns:
    - Total extractions (all time)
    - Monthly extractions (current month)
    - Remaining extractions this month
    - Plan limits
    """
    remaining = max(0, account.monthly_limit - account.monthly_extractions)
    usage_percentage = (account.monthly_extractions / account.monthly_limit * 100) if account.monthly_limit > 0 else 0

    return {
        "total_extractions": account.total_extractions,
        "monthly_extractions": account.monthly_extractions,
        "monthly_limit": account.monthly_limit,
        "remaining_this_month": remaining,
        "usage_percentage": round(usage_percentage, 2),
        "plan": account.plan,
        "is_near_limit": usage_percentage >= 80
    }


@router.get("/limits")
async def get_plan_info(
    account: Account = Depends(get_current_account)
):
    """
    Get plan limits and features.

    Shows what's included in current plan.
    """
    limits = get_plan_limits(account.plan)

    return {
        "plan": account.plan,
        "limits": limits,
        "enabled_models": account.enabled_models
    }
