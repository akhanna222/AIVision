"""
Template management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.db import crud
from app.core.auth import get_current_account
from app.db.models import Account

router = APIRouter()


# Request/Response models
class TemplateCreate(BaseModel):
    template_id: str
    template_name: str
    category: str
    country_id: int
    description: Optional[str] = None
    version: str = "1.0.0"
    fields: List[Dict[str, Any]]
    page_structure: Optional[Dict] = None
    tags: Optional[List[str]] = None


class TemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    page_structure: Optional[Dict] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: int
    template_id: str
    template_name: str
    category: str
    country_id: int
    description: Optional[str]
    version: str
    fields: List[Dict]
    tags: Optional[List[str]]
    is_custom: bool
    is_active: bool
    usage_count: int
    avg_confidence: float
    avg_completeness: float

    class Config:
        from_attributes = True


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Create custom template.

    **Field Structure:**
    ```json
    {
      "field_id": "employee_name",
      "field_name": "Employee Name",
      "field_type": "text",
      "required": true,
      "description": "Full name of employee",
      "validation_rules": {"min_length": 2},
      "examples": ["John Doe"]
    }
    ```
    """
    # Check if template_id already exists
    existing = crud.get_template_by_id(db, account.id, template_data.template_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template {template_data.template_id} already exists"
        )

    # Verify country exists
    country = crud.get_country_by_code(db, account.id, str(template_data.country_id))
    if not country:
        # Get country by ID instead
        countries = crud.get_countries(db, account.id)
        country = next((c for c in countries if c.id == template_data.country_id), None)
        if not country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Country {template_data.country_id} not found"
            )

    # Create template
    template = crud.create_template(
        db,
        account.id,
        {
            "template_id": template_data.template_id,
            "template_name": template_data.template_name,
            "category": template_data.category,
            "country_id": template_data.country_id,
            "description": template_data.description,
            "version": template_data.version,
            "fields": template_data.fields,
            "page_structure": template_data.page_structure,
            "tags": template_data.tags or [],
            "is_custom": True
        }
    )

    return template


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    country_id: Optional[int] = None,
    active_only: bool = True,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    List templates for account.

    **Filters:**
    - category: Filter by document category
    - country_id: Filter by country
    - active_only: Show only active templates (default: true)
    """
    templates = crud.get_templates(
        db,
        account.id,
        category=category,
        country_id=country_id,
        active_only=active_only
    )

    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get template by ID"""
    template = crud.get_template_by_id(db, account.id, template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    updates: TemplateUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Update template"""
    template = crud.get_template_by_id(db, account.id, template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    # Only allow updating custom templates
    if not template.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update default templates"
        )

    # Update template
    update_data = updates.dict(exclude_unset=True)
    updated_template = crud.update_template(
        db,
        account.id,
        template_id,
        update_data
    )

    return updated_template


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Delete template (soft delete)"""
    template = crud.get_template_by_id(db, account.id, template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    # Only allow deleting custom templates
    if not template.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete default templates"
        )

    success = crud.delete_template(db, account.id, template_id)

    if success:
        return {"message": "Template deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


@router.get("/{template_id}/stats")
async def get_template_stats(
    template_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Get template usage statistics.

    Returns:
    - Usage count
    - Average confidence
    - Average completeness
    - Success rate
    """
    template = crud.get_template_by_id(db, account.id, template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return {
        "template_id": template.template_id,
        "template_name": template.template_name,
        "usage_count": template.usage_count,
        "avg_confidence": round(template.avg_confidence, 3),
        "avg_completeness": round(template.avg_completeness, 3),
        "quality_grade": (
            "A" if template.avg_completeness >= 0.9 and template.avg_confidence >= 0.9
            else "B" if template.avg_completeness >= 0.8 and template.avg_confidence >= 0.8
            else "C" if template.avg_completeness >= 0.7 and template.avg_confidence >= 0.7
            else "D" if template.avg_completeness >= 0.6 and template.avg_confidence >= 0.6
            else "F"
        )
    }
