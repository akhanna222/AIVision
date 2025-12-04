"""
Country management API endpoints.
Dynamic country codes - accounts can add custom countries.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.db import crud
from app.core.auth import get_current_account
from app.db.models import Account

router = APIRouter()


# Request/Response models
class CountryCreate(BaseModel):
    code: str  # ISO 3166-1 alpha-2 or alpha-3
    name: str
    is_active: bool = True


class CountryResponse(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool
    is_default: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    country_data: CountryCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Create custom country.

    Allows accounts to add custom country codes for their specific needs.

    **Example:**
    ```json
    {
      "code": "EU",
      "name": "European Union",
      "is_active": true
    }
    ```
    """
    # Check if country code already exists
    existing = crud.get_country_by_code(db, account.id, country_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Country code {country_data.code} already exists"
        )

    # Create country
    country = crud.create_country(
        db,
        account_id=account.id,
        code=country_data.code,
        name=country_data.name,
        is_active=country_data.is_active
    )

    return country


@router.get("/", response_model=List[CountryResponse])
async def list_countries(
    active_only: bool = True,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    List countries for account.

    Includes both default countries (IE, GB, US, etc.) and custom countries.

    **Parameters:**
    - active_only: Show only active countries (default: true)
    """
    countries = crud.get_countries(db, account.id, active_only=active_only)

    return countries


@router.get("/{country_code}", response_model=CountryResponse)
async def get_country(
    country_code: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get country by code"""
    country = crud.get_country_by_code(db, account.id, country_code)

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country {country_code} not found"
        )

    return country


@router.patch("/{country_code}/activate")
async def activate_country(
    country_code: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Activate country"""
    country = crud.get_country_by_code(db, account.id, country_code)

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country {country_code} not found"
        )

    country.is_active = True
    db.commit()

    return {"message": f"Country {country_code} activated"}


@router.patch("/{country_code}/deactivate")
async def deactivate_country(
    country_code: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Deactivate country"""
    country = crud.get_country_by_code(db, account.id, country_code)

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country {country_code} not found"
        )

    # Don't allow deactivating default countries
    if country.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate default countries"
        )

    country.is_active = False
    db.commit()

    return {"message": f"Country {country_code} deactivated"}
