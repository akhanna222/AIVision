"""
Categories management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.core.auth import get_current_account
from app.db.models import Account
from app.db import crud

router = APIRouter()


class CategoryCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    icon: str = "📁"
    color: str = "blue"


class CategoryUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    icon: str
    color: str
    is_default: bool
    template_count: int
    extraction_count: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """List all categories for account."""
    # Initialize default categories if none exist
    existing = crud.get_categories(db, account.id, active_only=False)
    if not existing:
        crud.init_default_categories(db, account.id)
        existing = crud.get_categories(db, account.id, active_only=False)

    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            display_name=c.display_name,
            description=c.description,
            icon=c.icon or "📁",
            color=c.color or "blue",
            is_default=c.is_default,
            template_count=c.template_count,
            extraction_count=c.extraction_count,
            created_at=c.created_at.isoformat() if c.created_at else ""
        )
        for c in existing
    ]


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Create a custom category."""
    # Check for duplicate
    existing = crud.get_categories(db, account.id, active_only=False)
    name_normalized = data.name.lower().replace(" ", "_")
    if any(c.name == name_normalized for c in existing):
        raise HTTPException(status_code=400, detail="Category already exists")

    category = crud.create_category(
        db,
        account_id=account.id,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        icon=data.icon,
        color=data.color
    )
    return CategoryResponse(
        id=category.id,
        name=category.name,
        display_name=category.display_name,
        description=category.description,
        icon=category.icon or "📁",
        color=category.color or "blue",
        is_default=category.is_default,
        template_count=category.template_count,
        extraction_count=category.extraction_count,
        created_at=category.created_at.isoformat() if category.created_at else ""
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get category by ID."""
    category = crud.get_category_by_id(db, account.id, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse(
        id=category.id,
        name=category.name,
        display_name=category.display_name,
        description=category.description,
        icon=category.icon or "📁",
        color=category.color or "blue",
        is_default=category.is_default,
        template_count=category.template_count,
        extraction_count=category.extraction_count,
        created_at=category.created_at.isoformat() if category.created_at else ""
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    updates: CategoryUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Update category (custom categories only)."""
    category = crud.get_category_by_id(db, account.id, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.is_default:
        raise HTTPException(status_code=400, detail="Cannot modify default categories")

    category = crud.update_category(
        db, account.id, category_id,
        {k: v for k, v in updates.model_dump().items() if v is not None}
    )
    return CategoryResponse(
        id=category.id,
        name=category.name,
        display_name=category.display_name,
        description=category.description,
        icon=category.icon or "📁",
        color=category.color or "blue",
        is_default=category.is_default,
        template_count=category.template_count,
        extraction_count=category.extraction_count,
        created_at=category.created_at.isoformat() if category.created_at else ""
    )


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Delete category (custom categories only)."""
    category = crud.get_category_by_id(db, account.id, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default categories")

    crud.delete_category(db, account.id, category_id)
    return {"message": "Category deleted"}
