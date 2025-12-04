"""
Models package for AIVision document extraction service.
Exports all models and default templates.
"""

from .templates import (
    CountryCode,
    DocumentCategory,
    FieldType,
    FieldDefinition,
    DocumentTemplate,
    ExtractedField,
    BankTransaction,
    BankStatementPage
)

from .extraction import (
    VisionModel,
    ExtractionStatus,
    ExtractionRequest,
    ValidationResult,
    ProcessingMetadata,
    ExtractionResult,
    BatchExtractionRequest,
    BatchExtractionResult,
    ExportFormat,
    ExportRequest
)

from .default_templates import (
    IRELAND_MORTGAGE_APPLICATION,
    IRELAND_BANK_STATEMENT,
    UK_MORTGAGE_APPLICATION,
    US_MORTGAGE_APPLICATION,
    PASSPORT_UNIVERSAL,
    RECEIPT_UNIVERSAL,
    DEFAULT_TEMPLATES
)

__all__ = [
    # Template models
    "CountryCode",
    "DocumentCategory",
    "FieldType",
    "FieldDefinition",
    "DocumentTemplate",
    "ExtractedField",
    "BankTransaction",
    "BankStatementPage",

    # Extraction models
    "VisionModel",
    "ExtractionStatus",
    "ExtractionRequest",
    "ValidationResult",
    "ProcessingMetadata",
    "ExtractionResult",
    "BatchExtractionRequest",
    "BatchExtractionResult",
    "ExportFormat",
    "ExportRequest",

    # Default templates
    "IRELAND_MORTGAGE_APPLICATION",
    "IRELAND_BANK_STATEMENT",
    "UK_MORTGAGE_APPLICATION",
    "US_MORTGAGE_APPLICATION",
    "PASSPORT_UNIVERSAL",
    "RECEIPT_UNIVERSAL",
    "DEFAULT_TEMPLATES"
]
