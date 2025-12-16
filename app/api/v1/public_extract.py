"""
Public Extraction API - No Authentication Required
Extract documents using saved templates by name
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db.session import get_db
from app.db import crud
from app.core.extraction_service import ExtractionService
from app.services.multi_model_extractor import MultiModelExtractor, ModelStrategy
from app.config import settings, get_api_keys
from app.models import VisionModel

router = APIRouter()
extraction_service = ExtractionService()
multi_model_extractor = MultiModelExtractor(extraction_service)


@router.post("/extract/{template_name}")
async def extract_with_template_name(
    template_name: str,
    file: UploadFile = File(...),
    vision_model: str = Form("gemini-2.0-flash-exp"),
    use_multi_model: bool = Form(False),
    models: Optional[str] = Form(None),  # Comma-separated if use_multi_model=True
    strategy: str = Form("hybrid"),
    db: Session = Depends(get_db)
):
    """
    Extract document using a saved template name - NO AUTH REQUIRED!

    **URL Format**: `/api/v1/public/extract/{template_name}`

    **Example**:
    ```
    POST /api/v1/public/extract/my_invoice_template
    ```

    **Parameters**:
    - template_name: Name/ID of the saved template (in URL path)
    - file: Document to extract (PDF or image)
    - vision_model: Model to use (default: gemini-2.0-flash-exp)
    - use_multi_model: Enable multi-model extraction (default: false)
    - models: Comma-separated models (if use_multi_model=true)
    - strategy: sequential, parallel, or hybrid (default: hybrid)

    **Returns**: Extracted fields matching your template
    """
    # Validate file size
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)

    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Validate file extension
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Get public account and template
    public_account = crud.get_account_by_email(db, "public@aivision.local")

    if not public_account:
        raise HTTPException(
            status_code=404,
            detail="Public templates not initialized. Create a template first."
        )

    # Find template by ID or name
    template = crud.get_template_by_id(db, public_account.id, template_name)

    if not template:
        # Try to find by template_name field
        templates = crud.get_templates(db, public_account.id)
        template = next(
            (t for t in templates if t.template_name.lower() == template_name.lower()),
            None
        )

    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Create it first or use a default template."
        )

    # Prepare template dict
    template_dict = {
        "template_id": template.template_id,
        "template_name": template.template_name,
        "category": template.category,
        "fields": template.fields
    }

    # Create extraction record
    extraction_id = f"ext_{uuid.uuid4().hex[:16]}"
    extraction_record = crud.create_extraction(
        db,
        {
            "extraction_id": extraction_id,
            "account_id": public_account.id,
            "template_id": template.id,
            "filename": file.filename,
            "file_size_bytes": len(file_bytes),
            "vision_model": vision_model,
            "status": "processing"
        }
    )

    try:
        if use_multi_model and models:
            # Multi-model extraction
            model_list = [VisionModel(m.strip()) for m in models.split(",")]
            extraction_strategy = ModelStrategy(strategy)

            result = await multi_model_extractor.extract_with_multi_model(
                image_bytes=file_bytes,
                template=template_dict,
                models=model_list,
                api_keys=get_api_keys(),
                strategy=extraction_strategy
            )

            # Format response
            extracted_fields_list = []
            for field_name, value in result.extracted_fields.items():
                extracted_fields_list.append({
                    "field_name": field_name,
                    "value": value,
                    "confidence": result.field_confidences.get(field_name, 0.0),
                    "extracted_by": result.field_model_map.get(field_name, "unknown")
                })

            # Update extraction record
            crud.update_extraction(
                db,
                extraction_id,
                {
                    "status": "completed",
                    "extracted_fields": extracted_fields_list,
                    "completeness_score": result.overall_completeness,
                    "average_confidence": result.overall_confidence,
                    "field_model_map": {k: (v.value if hasattr(v, 'value') else str(v))
                                       for k, v in result.field_model_map.items()},
                    "extraction_summary": result.extraction_summary,
                    "models_tried": [m.value if hasattr(m, 'value') else str(m)
                                    for m in result.models_tried],
                }
            )

            # Update template usage
            crud.update_template_stats(
                db,
                template.id,
                result.overall_confidence,
                result.overall_completeness
            )

            return {
                "extraction_id": extraction_id,
                "template_name": template.template_name,
                "template_id": template.template_id,
                "status": "completed",
                "extracted_fields": extracted_fields_list,
                "field_model_map": {k: (v.value if hasattr(v, 'value') else str(v))
                                   for k, v in result.field_model_map.items()},
                "multi_model_tracking": {
                    "models_tried": [m.value if hasattr(m, 'value') else str(m)
                                    for m in result.models_tried],
                    "extraction_summary": result.extraction_summary,
                    "completeness": result.overall_completeness,
                    "confidence": result.overall_confidence
                }
            }

        else:
            # Single model extraction
            result = await extraction_service.extract(
                document_bytes=file_bytes,
                filename=file.filename,
                template=template,
                account=public_account,
                vision_model=VisionModel(vision_model),
                api_keys=get_api_keys(),
                auto_detect=False
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
                }
            )

            # Update template stats
            crud.update_template_stats(
                db,
                template.id,
                result.validation.average_confidence,
                result.validation.completeness_score
            )

            return {
                "extraction_id": extraction_id,
                "template_name": template.template_name,
                "template_id": template.template_id,
                "status": result.status.value,
                "extracted_fields": [f.dict() for f in result.extracted_fields],
                "validation": {
                    "completeness_score": result.validation.completeness_score,
                    "average_confidence": result.validation.average_confidence,
                    "quality_grade": result.validation.quality_grade,
                }
            }

    except Exception as e:
        # Update as failed
        crud.update_extraction(
            db,
            extraction_id,
            {
                "status": "failed",
                "error_message": str(e)
            }
        )

        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@router.get("/templates")
async def list_available_templates(db: Session = Depends(get_db)):
    """
    List all available template names for extraction
    """
    public_account = crud.get_account_by_email(db, "public@aivision.local")

    if not public_account:
        return {"templates": []}

    templates = crud.get_templates(db, public_account.id)

    return {
        "templates": [
            {
                "template_id": t.template_id,
                "template_name": t.template_name,
                "category": t.category,
                "usage_count": t.usage_count,
                "api_endpoint": f"/api/v1/public/extract/{t.template_id}"
            }
            for t in templates
        ]
    }
