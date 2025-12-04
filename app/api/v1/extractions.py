"""
Document extraction API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import uuid
import json
import io
import csv

from app.db.session import get_db
from app.db import crud
from app.core.auth import get_current_account, can_use_model
from app.core.extraction_service import ExtractionService
from app.config import settings, get_api_keys
from app.db.models import Account
from app.models import VisionModel, ExtractionStatus

router = APIRouter()
extraction_service = ExtractionService()


# Request/Response models
class ExtractionRequest(BaseModel):
    template_id: Optional[str] = None
    vision_model: str = "gemini-2.0-flash-exp"
    fallback_models: Optional[List[str]] = None
    confidence_threshold: float = 0.7
    auto_detect: bool = True


class ExtractionListResponse(BaseModel):
    extraction_id: str
    filename: str
    status: str
    quality_grade: Optional[str]
    completeness_score: float
    created_at: str
    template_name: str


@router.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    template_id: Optional[str] = Form(None),
    vision_model: str = Form("gemini-2.0-flash-exp"),
    fallback_models: Optional[str] = Form(None),
    confidence_threshold: float = Form(0.7),
    auto_detect: bool = Form(True),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Extract data from document.

    **Parameters:**
    - file: PDF or image file (max 50MB)
    - template_id: Template to use (optional if auto_detect=true)
    - vision_model: gemini-2.0-flash-exp, gpt-4o, claude-sonnet-4-20250514
    - fallback_models: Comma-separated list of fallback models
    - confidence_threshold: Minimum confidence (0.0-1.0)
    - auto_detect: Auto-detect document category and generate tags

    **Returns:**
    Extraction result with extracted fields, validation, and quality score.
    """
    # Validate file size
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)

    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Validate file extension
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Check if model is allowed for account
    if not can_use_model(account, vision_model):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Model {vision_model} not available in your plan"
        )

    # Get template
    template = None
    if template_id:
        template = crud.get_template_by_id(db, account.id, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )
    elif not auto_detect:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either template_id or auto_detect must be provided"
        )

    # Parse fallback models
    fallback_model_list = None
    if fallback_models:
        fallback_model_list = [
            VisionModel(m.strip())
            for m in fallback_models.split(",")
        ]

    # Create extraction record
    extraction_id = f"ext_{uuid.uuid4().hex[:16]}"
    extraction_record = crud.create_extraction(
        db,
        {
            "extraction_id": extraction_id,
            "account_id": account.id,
            "template_id": template.id if template else None,
            "filename": file.filename,
            "file_size_bytes": len(file_bytes),
            "vision_model": vision_model,
            "fallback_models": fallback_model_list or [],
            "confidence_threshold": confidence_threshold,
            "status": "processing"
        }
    )

    try:
        # Perform extraction
        result = await extraction_service.extract(
            document_bytes=file_bytes,
            filename=file.filename,
            template=template,
            account=account,
            vision_model=VisionModel(vision_model),
            api_keys=get_api_keys(),
            fallback_models=fallback_model_list,
            confidence_threshold=confidence_threshold,
            auto_detect=auto_detect
        )

        # Update extraction record
        crud.update_extraction(
            db,
            extraction_id,
            {
                "status": result.status.value,
                "extracted_fields": [f.dict() for f in result.extracted_fields],
                "completeness_score": result.validation.completeness_score,
                "average_confidence": result.validation.average_confidence,
                "quality_grade": result.validation.quality_grade,
                "missing_required_fields": result.validation.missing_required_fields,
                "low_confidence_fields": result.validation.low_confidence_fields,
                "validation_errors": result.validation.validation_errors,
                "processing_time_ms": result.processing.processing_time_ms,
                "cost_usd": result.processing.cost_usd,
                "fallback_used": result.processing.fallback_used,
                "retry_count": result.processing.retry_count,
                "completed_at": result.processing.timestamp
            }
        )

        # Update account usage
        crud.update_account_usage(db, account.id, extractions=1)

        # Log usage
        crud.log_usage(
            db,
            account_id=account.id,
            operation="extract",
            vision_model=result.processing.vision_model_used.value,
            pages_processed=result.total_pages,
            tokens_used=0,  # TODO: Get from model response
            cost_usd=result.processing.cost_usd,
            success=True,
            processing_time_ms=result.processing.processing_time_ms,
            extraction_id=extraction_id
        )

        # Update template stats if template was used
        if template:
            crud.update_template_stats(
                db,
                template.id,
                result.validation.average_confidence,
                result.validation.completeness_score
            )

        return result

    except Exception as e:
        # Update extraction as failed
        crud.update_extraction(
            db,
            extraction_id,
            {
                "status": "failed",
                "error_message": str(e)
            }
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )


@router.get("/{extraction_id}")
async def get_extraction(
    extraction_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Get extraction result by ID"""
    extraction = crud.get_extraction(db, account.id, extraction_id)

    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    return extraction


@router.get("/", response_model=List[ExtractionListResponse])
async def list_extractions(
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    List extractions for account.

    **Parameters:**
    - status: Filter by status (pending, processing, completed, failed)
    - limit: Maximum number of results (default 100)
    - offset: Pagination offset
    """
    extractions = crud.get_extractions(
        db,
        account.id,
        status=status_filter,
        limit=limit,
        offset=offset
    )

    return [
        ExtractionListResponse(
            extraction_id=e.extraction_id,
            filename=e.filename,
            status=e.status,
            quality_grade=e.quality_grade,
            completeness_score=e.completeness_score,
            created_at=e.created_at.isoformat(),
            template_name=e.template.template_name if e.template else "Auto-detected"
        )
        for e in extractions
    ]


@router.get("/{extraction_id}/export")
async def export_extraction(
    extraction_id: str,
    format: str = "json",
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """
    Export extraction result.

    **Formats:**
    - json: Structured JSON with all metadata
    - csv: Flattened CSV with field values
    - excel: Excel spreadsheet (future)
    """
    extraction = crud.get_extraction(db, account.id, extraction_id)

    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    if format == "json":
        return extraction

    elif format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Field ID", "Field Name", "Value", "Confidence", "Page"])

        # Data
        for field in extraction.extracted_fields:
            writer.writerow([
                field.get("field_id"),
                field.get("field_name"),
                field.get("value"),
                field.get("confidence"),
                field.get("page_number")
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={extraction_id}.csv"
            }
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}. Use json or csv"
        )


@router.delete("/{extraction_id}")
async def delete_extraction(
    extraction_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db)
):
    """Delete extraction (soft delete)"""
    extraction = crud.get_extraction(db, account.id, extraction_id)

    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )

    # Update status to deleted
    crud.update_extraction(
        db,
        extraction_id,
        {"status": "deleted"}
    )

    return {"message": "Extraction deleted successfully"}
