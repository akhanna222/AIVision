"""
Extraction service with validation, auto-tagging, and orchestration.
Coordinates vision models, templates, and validation.
"""

import logging
import uuid
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.models import (
    VisionModel, ExtractionRequest, ExtractionResult,
    ExtractionStatus, ValidationResult, ProcessingMetadata,
    ExtractedField, DocumentCategory
)
from app.services.vision import (
    GeminiClient, OpenAIClient, AnthropicClient,
    VisionModelError, VisionModelRateLimitError
)
from app.services.pdf_processor import PDFProcessor
from app.core.template_registry import get_template_registry
from app.db.models import Template, Account

logger = logging.getLogger(__name__)


class ExtractionService:
    """Main extraction service coordinating all components"""

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.template_registry = get_template_registry()

        # Vision model clients (lazy initialization)
        self._gemini_client = None
        self._openai_client = None
        self._anthropic_client = None

    def _get_vision_client(self, model: VisionModel, api_keys: Dict[str, str]):
        """Get vision model client (lazy initialization)"""
        if model == VisionModel.GEMINI_2_FLASH or model == VisionModel.GEMINI_2_5_PRO:
            if not self._gemini_client:
                self._gemini_client = GeminiClient(
                    api_key=api_keys.get("gemini"),
                    model_name=model.value
                )
            return self._gemini_client

        elif model in [VisionModel.GPT4O, VisionModel.GPT4O_MINI, VisionModel.GPT4_VISION]:
            if not self._openai_client:
                self._openai_client = OpenAIClient(
                    api_key=api_keys.get("openai"),
                    model_name=model.value
                )
            return self._openai_client

        elif model in [VisionModel.CLAUDE_SONNET_4, VisionModel.CLAUDE_OPUS_4]:
            if not self._anthropic_client:
                self._anthropic_client = AnthropicClient(
                    api_key=api_keys.get("anthropic"),
                    model_name=model.value
                )
            return self._anthropic_client

        raise ValueError(f"Unsupported vision model: {model}")

    async def auto_detect_category(
        self,
        image_bytes: bytes,
        model: VisionModel,
        api_keys: Dict[str, str]
    ) -> Tuple[DocumentCategory, float, str]:
        """
        Auto-detect document category and suggest tags.

        Returns:
            Tuple of (category, confidence, detected_country_code)
        """
        try:
            logger.info("Auto-detecting document category...")

            client = self._get_vision_client(model, api_keys)

            # Get all possible categories
            categories = [cat.value for cat in DocumentCategory]

            # Classify document
            classification = await client.classify_document(image_bytes, categories)

            # Find best match
            best_category = max(classification.items(), key=lambda x: x[1])
            category_name, confidence = best_category

            # Also try to detect country
            country_prompt = """Analyze this document and identify the country it's from.
Look for:
- Country-specific identifiers (PPS, NI, SSN, etc.)
- Currency symbols
- Address formats
- Language
- Regulatory text

Return JSON with:
{
  "country_code": "IE",  // ISO 3166-1 alpha-2/3
  "confidence": 0.95,
  "indicators": ["PPS Number visible", "EUR currency", "Irish address format"]
}"""

            country_result = await client.extract(
                image_bytes=image_bytes,
                prompt=country_prompt,
                temperature=0.0,
                max_tokens=200
            )

            detected_country = country_result.get("country_code", "UNKNOWN")

            logger.info(
                f"Auto-detected: {category_name} (confidence: {confidence:.2f}), "
                f"Country: {detected_country}"
            )

            return DocumentCategory(category_name), confidence, detected_country

        except Exception as e:
            logger.error(f"Auto-detection failed: {e}")
            # Return default
            return DocumentCategory.RECEIPT, 0.0, "UNKNOWN"

    async def generate_auto_tags(
        self,
        image_bytes: bytes,
        extracted_fields: List[Dict],
        category: DocumentCategory,
        model: VisionModel,
        api_keys: Dict[str, str]
    ) -> List[str]:
        """
        Generate automatic tags for document based on content.

        Returns:
            List of auto-generated tags
        """
        try:
            logger.info("Generating auto tags...")

            # Base tags from category
            tags = [category.value]

            # Extract key information for tagging
            tag_prompt = f"""Analyze this {category.value} document and generate relevant tags.

Consider:
- Document type/subtype
- Key entities (companies, people)
- Date ranges or periods
- Geographic location
- Document purpose
- Special attributes

Generate 3-5 concise tags (max 3 words each).

Return JSON:
{{
  "tags": ["mortgage_application", "property_purchase", "2024", "ireland", "first_time_buyer"]
}}"""

            client = self._get_vision_client(model, api_keys)
            result = await client.extract(
                image_bytes=image_bytes,
                prompt=tag_prompt,
                temperature=0.3,
                max_tokens=200
            )

            generated_tags = result.get("tags", [])
            tags.extend(generated_tags)

            # Add tags from extracted fields
            for field in extracted_fields:
                if field.get("field_id") == "employment_status":
                    tags.append(f"employment_{field.get('value', '').lower()}")
                elif field.get("field_id") == "first_time_buyer" and field.get("value"):
                    tags.append("first_time_buyer")

            # Remove duplicates and return
            unique_tags = list(set(tags))
            logger.info(f"Generated {len(unique_tags)} tags: {unique_tags}")

            return unique_tags

        except Exception as e:
            logger.error(f"Auto-tag generation failed: {e}")
            return [category.value]

    def validate_extraction(
        self,
        extracted_fields: List[ExtractedField],
        template: Template,
        confidence_threshold: float
    ) -> ValidationResult:
        """
        Validate extracted fields against template.

        Returns:
            ValidationResult with scores and missing fields
        """
        # Convert template fields from JSON
        template_fields = {f["field_id"]: f for f in template.fields}
        required_fields = {
            f["field_id"] for f in template.fields
            if f.get("required", False)
        }

        # Check what was extracted
        extracted_field_ids = {
            f.field_id for f in extracted_fields
            if f.extracted and f.value is not None
        }

        # Missing required fields
        missing_required = list(required_fields - extracted_field_ids)

        # Low confidence fields
        low_confidence = [
            f.field_id for f in extracted_fields
            if f.confidence < confidence_threshold
        ]

        # Calculate completeness
        if len(required_fields) > 0:
            completeness = len(required_fields & extracted_field_ids) / len(required_fields)
        else:
            completeness = 1.0

        # Calculate average confidence
        confidences = [f.confidence for f in extracted_fields if f.extracted]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Determine quality grade
        if completeness >= 0.9 and avg_confidence >= 0.9:
            grade = "A"
        elif completeness >= 0.8 and avg_confidence >= 0.8:
            grade = "B"
        elif completeness >= 0.7 and avg_confidence >= 0.7:
            grade = "C"
        elif completeness >= 0.6 and avg_confidence >= 0.6:
            grade = "D"
        else:
            grade = "F"

        # Validation errors
        errors = []
        for field in extracted_fields:
            if field.field_id in missing_required:
                errors.append({
                    "field_id": field.field_id,
                    "error": "Required field not found or empty"
                })
            elif field.field_id in low_confidence:
                errors.append({
                    "field_id": field.field_id,
                    "error": f"Low confidence: {field.confidence:.2f}"
                })

        is_valid = len(missing_required) == 0 and len(low_confidence) == 0

        return ValidationResult(
            is_valid=is_valid,
            completeness_score=completeness,
            average_confidence=avg_confidence,
            missing_required_fields=missing_required,
            low_confidence_fields=low_confidence,
            validation_errors=errors,
            quality_grade=grade
        )

    def build_extraction_prompt(
        self,
        template: Template,
        page_number: Optional[int] = None
    ) -> str:
        """Build extraction prompt for vision model"""
        fields_description = "\n".join([
            f"- {field['field_id']} ({field['field_name']}): {field['description']}"
            + (f" [Examples: {', '.join(field.get('examples', []))}]" if field.get('examples') else "")
            + (" [REQUIRED]" if field.get('required') else " [Optional]")
            for field in template.fields
        ])

        page_context = f"\nThis is page {page_number} of the document." if page_number else ""

        return f"""Extract the following fields from this {template.template_name} document:

{fields_description}{page_context}

Important instructions:
1. Extract ONLY information explicitly present in the document
2. Return null for fields not found
3. Maintain original formatting for dates, numbers, currency
4. For currency values, extract the number without symbols
5. Extract text exactly as it appears
6. Provide a confidence score (0.0-1.0) for each field

Return a JSON object with this structure:
{{
  "extracted_fields": [
    {{
      "field_id": "field_identifier",
      "value": "extracted_value or null",
      "confidence": 0.95,
      "page_number": {page_number or 1}
    }}
  ]
}}

Return ONLY valid JSON, no additional commentary."""

    async def extract(
        self,
        document_bytes: bytes,
        filename: str,
        template: Template,
        account: Account,
        vision_model: VisionModel,
        api_keys: Dict[str, str],
        fallback_models: Optional[List[VisionModel]] = None,
        confidence_threshold: float = 0.7,
        auto_detect: bool = False
    ) -> ExtractionResult:
        """
        Main extraction method.

        Args:
            document_bytes: PDF or image bytes
            filename: Original filename
            template: Template to use
            account: Account performing extraction
            vision_model: Primary vision model
            api_keys: Dict of API keys
            fallback_models: Fallback models if primary fails
            confidence_threshold: Minimum confidence threshold
            auto_detect: Auto-detect category and tags

        Returns:
            ExtractionResult
        """
        start_time = time.time()
        extraction_id = f"ext_{uuid.uuid4().hex[:16]}"

        logger.info(f"Starting extraction {extraction_id} for {filename}")

        try:
            # Validate PDF and get info
            pdf_info = self.pdf_processor.get_pdf_info(document_bytes)
            total_pages = pdf_info["num_pages"]

            # Convert PDF to images
            logger.info(f"Converting {total_pages} pages to images...")
            images = self.pdf_processor.convert_pdf_to_images(document_bytes)

            # Auto-detect category if requested
            detected_category = None
            detected_country = None
            if auto_detect:
                detected_category, detect_confidence, detected_country = await self.auto_detect_category(
                    images[0], vision_model, api_keys
                )
                logger.info(f"Detected category: {detected_category} (confidence: {detect_confidence:.2f})")

            # Extract from each page
            all_extracted_fields = []
            models_used = [vision_model]
            fallback_used = False

            for page_num, image_bytes in enumerate(images, start=1):
                logger.info(f"Extracting from page {page_num}/{total_pages}...")

                prompt = self.build_extraction_prompt(template, page_num)

                # Try primary model
                try:
                    client = self._get_vision_client(vision_model, api_keys)
                    result = await client.extract(
                        image_bytes=image_bytes,
                        prompt=prompt,
                        temperature=0.0
                    )

                    # Parse extracted fields
                    for field_data in result.get("extracted_fields", []):
                        all_extracted_fields.append(ExtractedField(
                            field_id=field_data["field_id"],
                            field_name=field_data["field_id"].replace("_", " ").title(),
                            value=field_data.get("value"),
                            confidence=field_data.get("confidence", 0.0),
                            extracted=field_data.get("value") is not None,
                            page_number=page_num
                        ))

                except (VisionModelError, VisionModelRateLimitError) as e:
                    logger.warning(f"Primary model failed: {e}")

                    # Try fallback models
                    if fallback_models:
                        for fallback_model in fallback_models:
                            try:
                                logger.info(f"Trying fallback model: {fallback_model}")
                                client = self._get_vision_client(fallback_model, api_keys)
                                result = await client.extract(
                                    image_bytes=image_bytes,
                                    prompt=prompt,
                                    temperature=0.0
                                )

                                # Parse fields
                                for field_data in result.get("extracted_fields", []):
                                    all_extracted_fields.append(ExtractedField(
                                        field_id=field_data["field_id"],
                                        field_name=field_data["field_id"].replace("_", " ").title(),
                                        value=field_data.get("value"),
                                        confidence=field_data.get("confidence", 0.0),
                                        extracted=field_data.get("value") is not None,
                                        page_number=page_num
                                    ))

                                models_used.append(fallback_model)
                                fallback_used = True
                                break

                            except Exception as fallback_error:
                                logger.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                                continue

            # Validate extraction
            validation = self.validate_extraction(
                all_extracted_fields,
                template,
                confidence_threshold
            )

            # Generate auto tags
            auto_tags = []
            if auto_detect:
                auto_tags = await self.generate_auto_tags(
                    images[0],
                    [{"field_id": f.field_id, "value": f.value} for f in all_extracted_fields],
                    detected_category or DocumentCategory(template.category),
                    vision_model,
                    api_keys
                )

            # Calculate processing time and cost
            processing_time_ms = int((time.time() - start_time) * 1000)
            cost_usd = self._estimate_cost(vision_model, total_pages)

            # Build result
            result = ExtractionResult(
                extraction_id=extraction_id,
                document_id=f"doc_{uuid.uuid4().hex[:16]}",
                status=ExtractionStatus.COMPLETED,
                template_id=template.template_id,
                template_name=template.template_name,
                category=DocumentCategory(template.category),
                country=template.country.code if hasattr(template, 'country') else "UNKNOWN",
                filename=filename,
                total_pages=total_pages,
                file_size_bytes=len(document_bytes),
                extracted_fields=all_extracted_fields,
                validation=validation,
                processing=ProcessingMetadata(
                    vision_model_used=models_used[0],
                    processing_time_ms=processing_time_ms,
                    cost_usd=cost_usd,
                    pages_processed=total_pages,
                    fallback_used=fallback_used,
                    retry_count=len(models_used) - 1,
                    timestamp=datetime.utcnow()
                )
            )

            logger.info(
                f"Extraction {extraction_id} completed: "
                f"Grade {validation.quality_grade}, "
                f"Completeness {validation.completeness_score:.1%}, "
                f"Time {processing_time_ms}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Extraction {extraction_id} failed: {e}")
            raise

    def _estimate_cost(self, model: VisionModel, pages: int) -> float:
        """Estimate extraction cost"""
        # Cost per page estimates
        cost_per_page = {
            VisionModel.GEMINI_2_FLASH: 0.03,
            VisionModel.GEMINI_2_5_PRO: 0.10,
            VisionModel.GPT4O: 0.15,
            VisionModel.GPT4O_MINI: 0.05,
            VisionModel.CLAUDE_SONNET_4: 0.12,
            VisionModel.CLAUDE_OPUS_4: 0.25
        }

        return cost_per_page.get(model, 0.05) * pages
