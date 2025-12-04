"""
Template models for document extraction.
Defines document templates, field definitions, and default templates for various document types.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CountryCode(str, Enum):
    """Supported countries for document templates"""
    IRELAND = "IE"
    UNITED_KINGDOM = "GB"
    UNITED_STATES = "US"
    CANADA = "CA"
    AUSTRALIA = "AU"


class DocumentCategory(str, Enum):
    """Document type categories"""
    # Mortgage Documents
    MORTGAGE_APPLICATION = "mortgage_application"
    PROOF_OF_INCOME = "proof_of_income"
    EMPLOYMENT_VERIFICATION = "employment_verification"
    BANK_STATEMENT = "bank_statement"
    TAX_RETURN = "tax_return"
    PROPERTY_VALUATION = "property_valuation"
    CREDIT_REPORT = "credit_report"
    MORTGAGE_STATEMENT = "mortgage_statement"

    # Identity Documents
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"

    # Financial Documents
    PAYSLIP = "payslip"
    RECEIPT = "receipt"
    INVOICE = "invoice"
    UTILITY_BILL = "utility_bill"


class FieldType(str, Enum):
    """Field data types for extraction"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    ADDRESS = "address"
    PHONE = "phone"
    EMAIL = "email"
    PERCENTAGE = "percentage"
    URL = "url"


class FieldDefinition(BaseModel):
    """Individual field definition in a template"""
    field_id: str = Field(..., description="Unique field identifier (snake_case)")
    field_name: str = Field(..., description="Human-readable field name")
    field_type: FieldType = Field(..., description="Data type of the field")
    required: bool = Field(default=True, description="Whether field is mandatory")
    description: str = Field(
        ...,
        description="Detailed description for AI model to understand context"
    )
    validation_rules: Optional[Dict] = Field(
        default=None,
        description="Validation rules (regex pattern, min/max, currency, etc.)"
    )
    examples: Optional[List[str]] = Field(
        default=None,
        description="Example values to guide AI extraction"
    )
    extraction_hints: Optional[str] = Field(
        default=None,
        description="Additional hints for the AI model"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "field_id": "applicant_name",
                "field_name": "Applicant Full Name",
                "field_type": "text",
                "required": True,
                "description": "Primary applicant's full legal name as it appears on ID",
                "validation_rules": {"min_length": 2, "max_length": 100},
                "examples": ["John Michael O'Brien", "Mary Kate Murphy"],
                "extraction_hints": "Usually found in the first section of the form"
            }
        }


class DocumentTemplate(BaseModel):
    """Template definition for document extraction"""
    template_id: str = Field(..., description="Unique template identifier")
    category: DocumentCategory = Field(..., description="Document category")
    country: CountryCode = Field(..., description="Country-specific template")
    template_name: str = Field(..., description="Human-readable template name")
    description: str = Field(..., description="Template description")
    version: str = Field(default="1.0.0", description="Template version")
    fields: List[FieldDefinition] = Field(..., description="Field definitions")
    page_structure: Optional[Dict] = Field(
        default=None,
        description="Expected page structure for multi-page documents"
    )
    custom: bool = Field(
        default=False,
        description="Whether this is a user-created custom template"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags for template categorization"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "ie_mortgage_app_v1",
                "category": "mortgage_application",
                "country": "IE",
                "template_name": "Irish Mortgage Application Form",
                "description": "Standard mortgage application for Irish banks",
                "version": "1.0.0",
                "fields": [],
                "page_structure": {
                    "total_pages": "variable",
                    "personal_info_page": 1,
                    "financial_info_page": 2
                },
                "custom": False,
                "tags": ["mortgage", "ireland", "banking"]
            }
        }


class ExtractedField(BaseModel):
    """Extracted field with metadata"""
    field_id: str = Field(..., description="Field identifier from template")
    field_name: str = Field(..., description="Human-readable field name")
    value: Optional[str] = Field(None, description="Extracted value")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from AI model"
    )
    extracted: bool = Field(..., description="Whether field was successfully extracted")
    page_number: Optional[int] = Field(
        None,
        description="Page number where field was found"
    )
    bounding_box: Optional[Dict[str, int]] = Field(
        None,
        description="Bounding box coordinates {x, y, width, height}"
    )
    validation_errors: Optional[List[str]] = Field(
        default=None,
        description="Validation errors if any"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "field_id": "applicant_name",
                "field_name": "Applicant Full Name",
                "value": "John Michael O'Brien",
                "confidence": 0.98,
                "extracted": True,
                "page_number": 1,
                "bounding_box": {"x": 120, "y": 340, "width": 200, "height": 24},
                "validation_errors": None
            }
        }


class BankTransaction(BaseModel):
    """Individual bank transaction"""
    transaction_date: str = Field(..., description="Transaction date (YYYY-MM-DD)")
    description: str = Field(..., description="Transaction description/narrative")
    debit: Optional[float] = Field(None, description="Debit amount (negative)")
    credit: Optional[float] = Field(None, description="Credit amount (positive)")
    balance: Optional[float] = Field(None, description="Account balance after transaction")
    reference: Optional[str] = Field(None, description="Transaction reference/ID")
    category: Optional[str] = Field(None, description="Auto-categorized transaction type")


class BankStatementPage(BaseModel):
    """Bank statement page with transactions"""
    page_number: int = Field(..., description="Page number in the statement")
    transactions: List[BankTransaction] = Field(
        default_factory=list,
        description="List of transactions on this page"
    )
    page_opening_balance: Optional[float] = Field(
        None,
        description="Opening balance at start of page"
    )
    page_closing_balance: Optional[float] = Field(
        None,
        description="Closing balance at end of page"
    )
