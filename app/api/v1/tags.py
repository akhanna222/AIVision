"""
Tags management API endpoints.
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


class TagCreate(BaseModel):
    tag_name: str
    color: str = "blue"
    tag_category: Optional[str] = None


class TagUpdate(BaseModel):
    tag_name: Optional[str] = None
    color: Optional[str] = None
    tag_category: Optional[str] = None


class TagResponse(BaseModel):
    id: int
    tag_name: str
    color: str
    tag_category: Optional[str]
    usage_count: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TagResponse])
async def list_tags(
    category: Optional[str] = None,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """List all tags for account."""
    tags = crud.get_document_tags(db, account.id, category)
    return [
        TagResponse(
            id=t.id,
            tag_name=t.tag_name,
            color=t.color or "blue",
            tag_category=t.tag_category,
            usage_count=t.usage_count,
            created_at=t.created_at.isoformat() if t.created_at else ""
        )
        for t in tags
    ]


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Create a new tag."""
    # Check for duplicate
    existing_tags = crud.get_document_tags(db, account.id)
    if any(t.tag_name.lower() == tag_data.tag_name.lower() for t in existing_tags):
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = crud.create_document_tag(
        db,
        account_id=account.id,
        tag_name=tag_data.tag_name.lower(),
        color=tag_data.color,
        tag_category=tag_data.tag_category
    )
    return TagResponse(
        id=tag.id,
        tag_name=tag.tag_name,
        color=tag.color or "blue",
        tag_category=tag.tag_category,
        usage_count=tag.usage_count,
        created_at=tag.created_at.isoformat() if tag.created_at else ""
    )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get tag by ID."""
    tag = crud.get_document_tag_by_id(db, account.id, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return TagResponse(
        id=tag.id,
        tag_name=tag.tag_name,
        color=tag.color or "blue",
        tag_category=tag.tag_category,
        usage_count=tag.usage_count,
        created_at=tag.created_at.isoformat() if tag.created_at else ""
    )


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    updates: TagUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Update tag."""
    tag = crud.update_document_tag(
        db, account.id, tag_id,
        {k: v for k, v in updates.model_dump().items() if v is not None}
    )
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return TagResponse(
        id=tag.id,
        tag_name=tag.tag_name,
        color=tag.color or "blue",
        tag_category=tag.tag_category,
        usage_count=tag.usage_count,
        created_at=tag.created_at.isoformat() if tag.created_at else ""
    )


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Delete tag."""
    if not crud.delete_document_tag(db, account.id, tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted"}
