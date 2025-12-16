"""
Public Template API - No Authentication Required
Simple template builder for quick OCR extraction
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.db import crud
from app.db.models import Account

router = APIRouter()


# Request/Response Models
class TemplateFieldSchema(BaseModel):
    name: str
    type: str = "string"  # string, number, date, boolean
    description: str = ""
    required: bool = False


class PublicTemplateCreate(BaseModel):
    template_name: str
    category: str = "custom"
    description: str = ""
    fields: List[Dict[str, Any]]


class PublicTemplateResponse(BaseModel):
    template_id: str
    template_name: str
    category: str
    description: str
    fields: List[Dict[str, Any]]
    created_at: str
    usage_count: int


# Default templates library
DEFAULT_TEMPLATES = {
    "bank_statement": {
        "template_name": "Bank Statement",
        "category": "financial",
        "description": "Current account bank statement template",
        "fields": [
            {"name": "institution_name", "type": "string", "description": "Bank or credit union name", "required": True},
            {"name": "account_holder_name", "type": "string", "description": "Account holder full name", "required": True},
            {"name": "account_number", "type": "string", "description": "Account number", "required": True},
            {"name": "iban", "type": "string", "description": "IBAN", "required": False},
            {"name": "statement_start_date", "type": "date", "description": "Statement period start", "required": True},
            {"name": "statement_end_date", "type": "date", "description": "Statement period end", "required": True},
            {"name": "opening_balance", "type": "number", "description": "Opening balance", "required": True},
            {"name": "closing_balance", "type": "number", "description": "Closing balance", "required": True},
            {"name": "total_credits", "type": "number", "description": "Total credits", "required": False},
            {"name": "total_debits", "type": "number", "description": "Total debits", "required": False},
        ]
    },
    "invoice": {
        "template_name": "Invoice",
        "category": "financial",
        "description": "Standard invoice template",
        "fields": [
            {"name": "invoice_number", "type": "string", "description": "Invoice number", "required": True},
            {"name": "invoice_date", "type": "date", "description": "Invoice date", "required": True},
            {"name": "due_date", "type": "date", "description": "Payment due date", "required": False},
            {"name": "vendor_name", "type": "string", "description": "Vendor/supplier name", "required": True},
            {"name": "vendor_address", "type": "string", "description": "Vendor address", "required": False},
            {"name": "customer_name", "type": "string", "description": "Customer name", "required": True},
            {"name": "subtotal", "type": "number", "description": "Subtotal amount", "required": False},
            {"name": "tax_amount", "type": "number", "description": "Tax/VAT amount", "required": False},
            {"name": "total_amount", "type": "number", "description": "Total amount", "required": True},
            {"name": "currency", "type": "string", "description": "Currency code", "required": False},
        ]
    },
    "receipt": {
        "template_name": "Receipt",
        "category": "financial",
        "description": "Purchase receipt template",
        "fields": [
            {"name": "merchant_name", "type": "string", "description": "Merchant name", "required": True},
            {"name": "merchant_address", "type": "string", "description": "Merchant address", "required": False},
            {"name": "date", "type": "date", "description": "Purchase date", "required": True},
            {"name": "time", "type": "string", "description": "Purchase time", "required": False},
            {"name": "total_amount", "type": "number", "description": "Total amount", "required": True},
            {"name": "payment_method", "type": "string", "description": "Payment method", "required": False},
            {"name": "receipt_number", "type": "string", "description": "Receipt number", "required": False},
        ]
    },
    "payslip": {
        "template_name": "Payslip",
        "category": "employment",
        "description": "Employee payslip template",
        "fields": [
            {"name": "employee_name", "type": "string", "description": "Employee name", "required": True},
            {"name": "employee_id", "type": "string", "description": "Employee ID", "required": False},
            {"name": "employer_name", "type": "string", "description": "Employer name", "required": True},
            {"name": "pay_period_start", "type": "date", "description": "Pay period start", "required": True},
            {"name": "pay_period_end", "type": "date", "description": "Pay period end", "required": True},
            {"name": "pay_date", "type": "date", "description": "Payment date", "required": True},
            {"name": "gross_pay", "type": "number", "description": "Gross pay", "required": True},
            {"name": "tax_deducted", "type": "number", "description": "Tax deducted", "required": False},
            {"name": "net_pay", "type": "number", "description": "Net pay", "required": True},
        ]
    },
    "id_document": {
        "template_name": "ID Document",
        "category": "identification",
        "description": "Passport, driver's license, or ID card",
        "fields": [
            {"name": "document_type", "type": "string", "description": "Type of ID (passport, license, etc.)", "required": True},
            {"name": "document_number", "type": "string", "description": "Document number", "required": True},
            {"name": "full_name", "type": "string", "description": "Full name", "required": True},
            {"name": "date_of_birth", "type": "date", "description": "Date of birth", "required": True},
            {"name": "nationality", "type": "string", "description": "Nationality", "required": False},
            {"name": "issue_date", "type": "date", "description": "Issue date", "required": False},
            {"name": "expiry_date", "type": "date", "description": "Expiry date", "required": False},
            {"name": "issuing_authority", "type": "string", "description": "Issuing authority", "required": False},
        ]
    }
}


@router.get("/defaults")
async def get_default_templates():
    """Get list of default template names"""
    return {
        "templates": [
            {
                "template_id": key,
                "template_name": val["template_name"],
                "category": val["category"],
                "description": val["description"],
                "field_count": len(val["fields"])
            }
            for key, val in DEFAULT_TEMPLATES.items()
        ]
    }


@router.get("/defaults/{template_id}")
async def get_default_template(template_id: str):
    """Get a default template by ID"""
    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Default template '{template_id}' not found")

    return DEFAULT_TEMPLATES[template_id]


@router.post("/create", response_model=PublicTemplateResponse)
async def create_public_template(
    template_data: PublicTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a custom template - no authentication required!

    Templates are saved to a public account and can be accessed by name.
    """
    # Get or create a public/anonymous account for storing public templates
    public_account = crud.get_account_by_email(db, "public@aivision.local")

    if not public_account:
        # Create public account
        public_account = crud.create_account(
            db=db,
            name="Public Templates",
            email="public@aivision.local",
            plan="free"
        )

    # Get public country (Ireland default)
    country = crud.get_country_by_code(db, public_account.id, "IE")
    if not country:
        country = crud.create_country(
            db=db,
            account_id=public_account.id,
            code="IE",
            name="Ireland"
        )

    # Generate unique template_id from name
    base_id = template_data.template_name.lower().replace(" ", "_").replace("-", "_")
    template_id = f"{base_id}_{uuid.uuid4().hex[:8]}"

    # Create template
    template = crud.create_template(
        db=db,
        account_id=public_account.id,
        country_id=country.id,
        template_id=template_id,
        template_name=template_data.template_name,
        category=template_data.category,
        description=template_data.description,
        fields=template_data.fields,
        is_custom=True
    )

    return PublicTemplateResponse(
        template_id=template.template_id,
        template_name=template.template_name,
        category=template.category,
        description=template.description or "",
        fields=template.fields,
        created_at=template.created_at.isoformat(),
        usage_count=template.usage_count
    )


@router.get("/list", response_model=List[PublicTemplateResponse])
async def list_public_templates(
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all public templates (no auth required)
    """
    public_account = crud.get_account_by_email(db, "public@aivision.local")

    if not public_account:
        return []

    templates = crud.get_templates(
        db=db,
        account_id=public_account.id,
        category=category,
        limit=limit
    )

    return [
        PublicTemplateResponse(
            template_id=t.template_id,
            template_name=t.template_name,
            category=t.category,
            description=t.description or "",
            fields=t.fields,
            created_at=t.created_at.isoformat(),
            usage_count=t.usage_count
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=PublicTemplateResponse)
async def get_public_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a public template by ID
    """
    public_account = crud.get_account_by_email(db, "public@aivision.local")

    if not public_account:
        raise HTTPException(status_code=404, detail="Template not found")

    template = crud.get_template_by_id(db, public_account.id, template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    return PublicTemplateResponse(
        template_id=template.template_id,
        template_name=template.template_name,
        category=template.category,
        description=template.description or "",
        fields=template.fields,
        created_at=template.created_at.isoformat(),
        usage_count=template.usage_count
    )


@router.delete("/{template_id}")
async def delete_public_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a public template
    """
    public_account = crud.get_account_by_email(db, "public@aivision.local")

    if not public_account:
        raise HTTPException(status_code=404, detail="Template not found")

    template = crud.get_template_by_id(db, public_account.id, template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    # Delete template
    db.delete(template)
    db.commit()

    return {"message": f"Template '{template_id}' deleted successfully"}
