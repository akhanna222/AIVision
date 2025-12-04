"""
Extraction request and response models.
Defines the API contracts for document extraction operations.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .templates import (
    DocumentTemplate,
    DocumentCategory,
    CountryCode,
    ExtractedField,
    BankStatementPage
)


class VisionModel(str, Enum):
    """Supported vision models"""
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"
    GEMINI_2_5_PRO = "gemini-2.5-pro-preview"
    GPT4_VISION = "gpt-4-vision-preview"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"
    CLAUDE_OPUS_4 = "claude-opus-4-20250514"


class ExtractionStatus(str, Enum):
    """Extraction processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ExtractionRequest(BaseModel):
    """Request for document extraction"""
    template_id: Optional[str] = Field(
        default=None,
        description="Template ID to use. If None, auto-detect category."
    )
    custom_template: Optional[DocumentTemplate] = Field(
        default=None,
        description="Custom template definition (overrides template_id)"
    )
    vision_model: VisionModel = Field(
        default=VisionModel.GEMINI_2_FLASH,
        description="Primary vision model to use for extraction"
    )
    fallback_models: Optional[List[VisionModel]] = Field(
        default=None,
        description="Fallback models if primary fails"
    )
    enable_validation: bool = Field(
        default=True,
        description="Enable field validation and completeness check"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for field extraction"
    )
    auto_detect_category: bool = Field(
        default=True,
        description="Auto-detect document category if template_id is None"
    )
    extract_bounding_boxes: bool = Field(
        default=True,
        description="Extract bounding box coordinates for fields"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "ie_mortgage_app_v1",
                "vision_model": "gemini-2.0-flash-exp",
                "fallback_models": ["gpt-4o", "claude-sonnet-4-20250514"],
                "enable_validation": True,
                "confidence_threshold": 0.7,
                "auto_detect_category": True,
                "extract_bounding_boxes": True
            }
        }


class ValidationResult(BaseModel):
    """Validation result for extracted data"""
    is_valid: bool = Field(..., description="Overall validation status")
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of required fields extracted (0.0-1.0)"
    )
    average_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average confidence across all fields (0.0-1.0)"
    )
    missing_required_fields: List[str] = Field(
        default_factory=list,
        description="List of missing required field IDs"
    )
    low_confidence_fields: List[str] = Field(
        default_factory=list,
        description="Fields with confidence below threshold"
    )
    validation_errors: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    quality_grade: str = Field(
        ...,
        description="Quality grade: A (>90%), B (>80%), C (>70%), D (>60%), F (<60%)"
    )


class ProcessingMetadata(BaseModel):
    """Processing metadata for extraction"""
    vision_model_used: VisionModel = Field(..., description="Model that performed extraction")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")
    pages_processed: int = Field(..., description="Number of pages processed")
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback model was used"
    )
    retry_count: int = Field(default=0, description="Number of retries")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Processing timestamp"
    )


class ExtractionResult(BaseModel):
    """Complete extraction result"""
    extraction_id: str = Field(..., description="Unique extraction ID")
    document_id: str = Field(..., description="Document ID")
    status: ExtractionStatus = Field(..., description="Extraction status")

    # Template info
    template_id: str = Field(..., description="Template used")
    template_name: str = Field(..., description="Template display name")
    category: DocumentCategory = Field(..., description="Document category")
    country: CountryCode = Field(..., description="Document country")

    # Document info
    filename: str = Field(..., description="Original filename")
    total_pages: int = Field(..., description="Total number of pages")
    file_size_bytes: int = Field(..., description="File size in bytes")

    # Extracted data
    extracted_fields: List[ExtractedField] = Field(
        default_factory=list,
        description="List of extracted fields"
    )

    # Bank statement specific
    bank_statement_pages: Optional[List[BankStatementPage]] = Field(
        default=None,
        description="Page-by-page transactions for bank statements"
    )

    # Validation
    validation: ValidationResult = Field(..., description="Validation results")

    # Processing metadata
    processing: ProcessingMetadata = Field(..., description="Processing metadata")

    # Raw data
    raw_text: Optional[str] = Field(
        None,
        description="Full OCR text extracted from document"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "extraction_id": "ext_abc123",
                "document_id": "doc_xyz789",
                "status": "completed",
                "template_id": "ie_mortgage_app_v1",
                "template_name": "Irish Mortgage Application",
                "category": "mortgage_application",
                "country": "IE",
                "filename": "mortgage_application.pdf",
                "total_pages": 5,
                "file_size_bytes": 2048576,
                "extracted_fields": [],
                "validation": {
                    "is_valid": True,
                    "completeness_score": 0.95,
                    "average_confidence": 0.92,
                    "missing_required_fields": [],
                    "low_confidence_fields": [],
                    "validation_errors": [],
                    "quality_grade": "A"
                },
                "processing": {
                    "vision_model_used": "gemini-2.0-flash-exp",
                    "processing_time_ms": 3421,
                    "cost_usd": 0.05,
                    "pages_processed": 5,
                    "fallback_used": False,
                    "retry_count": 0,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }


class BatchExtractionRequest(BaseModel):
    """Request for batch document extraction"""
    documents: List[str] = Field(
        ...,
        description="List of document IDs to process"
    )
    template_id: Optional[str] = Field(
        default=None,
        description="Template ID to use for all documents"
    )
    vision_model: VisionModel = Field(
        default=VisionModel.GEMINI_2_FLASH,
        description="Vision model to use"
    )
    enable_validation: bool = Field(default=True)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class BatchExtractionResult(BaseModel):
    """Result of batch extraction"""
    batch_id: str = Field(..., description="Unique batch ID")
    total_documents: int = Field(..., description="Total documents in batch")
    completed: int = Field(..., description="Successfully completed")
    failed: int = Field(..., description="Failed extractions")
    pending: int = Field(..., description="Pending extractions")
    extractions: List[ExtractionResult] = Field(
        default_factory=list,
        description="Individual extraction results"
    )
    total_processing_time_ms: int = Field(..., description="Total processing time")
    total_cost_usd: Optional[float] = Field(None, description="Total cost")


class ExportFormat(str, Enum):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"


class ExportRequest(BaseModel):
    """Request for exporting extraction results"""
    extraction_id: str = Field(..., description="Extraction ID to export")
    format: ExportFormat = Field(..., description="Export format")
    include_metadata: bool = Field(
        default=True,
        description="Include processing metadata"
    )
    include_raw_text: bool = Field(
        default=False,
        description="Include raw OCR text"
    )
    flatten_nested: bool = Field(
        default=True,
        description="Flatten nested structures (for CSV)"
    )
