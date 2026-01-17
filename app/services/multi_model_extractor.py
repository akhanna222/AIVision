"""
Multi-Model Extraction Service

Advanced extraction service that supports:
1. Sequential model fallback (try models one by one)
2. Parallel model checking (run multiple models simultaneously)
3. Field-level model retry (retry specific fields with different models)
4. Confidence-based model selection
5. Extraction attempt tracking and reporting

This service significantly improves extraction accuracy by leveraging
multiple AI models and provides transparency about extraction attempts.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.models import VisionModel
from app.core.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


class ModelStrategy(str, Enum):
    """Strategy for using multiple models"""
    SEQUENTIAL = "sequential"  # Try models one by one
    PARALLEL = "parallel"      # Run all models simultaneously
    HYBRID = "hybrid"          # Try primary, then parallel for low-confidence fields


@dataclass
class FieldExtractionAttempt:
    """Tracks a single field extraction attempt"""
    field_name: str
    model: str
    value: Any
    confidence: float
    success: bool
    error: Optional[str] = None


@dataclass
class ModelAttempt:
    """Tracks a complete model extraction attempt"""
    model: str
    fields_extracted: Dict[str, Any]
    field_confidences: Dict[str, float]
    total_confidence: float
    completeness: float
    fields_missing: List[str]
    extraction_time_ms: int
    success: bool
    error: Optional[str] = None


@dataclass
class MultiModelExtractionResult:
    """Result of multi-model extraction with full tracking"""
    # Final extracted fields (best from all models)
    extracted_fields: Dict[str, Any]

    # Field-level model tracking
    field_model_map: Dict[str, str]  # Which model extracted each field
    field_confidences: Dict[str, float]

    # All model attempts
    model_attempts: List[ModelAttempt]

    # Fields that couldn't be extracted even after multiple attempts
    missing_fields: List[str]

    # Fields with low confidence (< threshold)
    low_confidence_fields: List[str]

    # Overall metrics
    overall_confidence: float
    overall_completeness: float
    models_tried: List[str]

    # User-friendly messages
    extraction_summary: str
    field_extraction_notes: Dict[str, str]  # Per-field notes about extraction

    # Strategy used
    strategy: ModelStrategy

    # Total time
    total_time_ms: int


class MultiModelExtractor:
    """
    Advanced extraction service using multiple models with fallback strategies.

    Features:
    - Sequential fallback: Try models one by one until confidence threshold met
    - Parallel extraction: Run multiple models and pick best results
    - Field-level retry: Re-extract specific fields with different models
    - Smart model selection based on document type
    - Detailed attempt tracking and reporting
    """

    def __init__(
        self,
        extraction_service: ExtractionService,
        default_strategy: ModelStrategy = ModelStrategy.SEQUENTIAL,
        confidence_threshold: float = 0.80,
        field_confidence_threshold: float = 0.70,
        max_models_to_try: int = 3
    ):
        self.extraction_service = extraction_service
        self.default_strategy = default_strategy
        self.confidence_threshold = confidence_threshold
        self.field_confidence_threshold = field_confidence_threshold
        self.max_models_to_try = max_models_to_try

    async def extract_with_multi_model(
        self,
        image_bytes: bytes,
        template: Dict[str, Any],
        models: List[VisionModel],
        api_keys: Dict[str, str],
        strategy: Optional[ModelStrategy] = None
    ) -> MultiModelExtractionResult:
        """
        Extract document fields using multiple models with specified strategy.

        Args:
            image_bytes: Image data
            template: Extraction template with field definitions
            models: List of models to try (in order for sequential)
            api_keys: API keys for vision models
            strategy: Extraction strategy (sequential, parallel, hybrid)

        Returns:
            MultiModelExtractionResult with complete tracking
        """
        import time
        start_time = time.time()

        strategy = strategy or self.default_strategy
        models = models[:self.max_models_to_try]  # Limit number of models

        logger.info(f"Starting multi-model extraction with {len(models)} models using {strategy} strategy")

        if strategy == ModelStrategy.SEQUENTIAL:
            result = await self._extract_sequential(image_bytes, template, models, api_keys)
        elif strategy == ModelStrategy.PARALLEL:
            result = await self._extract_parallel(image_bytes, template, models, api_keys)
        else:  # HYBRID
            result = await self._extract_hybrid(image_bytes, template, models, api_keys)

        result.total_time_ms = int((time.time() - start_time) * 1000)
        result.strategy = strategy

        # Generate user-friendly summary
        result.extraction_summary = self._generate_summary(result, template)
        result.field_extraction_notes = self._generate_field_notes(result, template)

        logger.info(f"Multi-model extraction completed: {len(result.extracted_fields)} fields extracted, "
                   f"{len(result.missing_fields)} missing, tried {len(result.models_tried)} models")

        return result

    async def _extract_sequential(
        self,
        image_bytes: bytes,
        template: Dict[str, Any],
        models: List[VisionModel],
        api_keys: Dict[str, str]
    ) -> MultiModelExtractionResult:
        """
        Sequential extraction: Try models one by one, stop when confidence is met.
        """
        model_attempts = []
        best_result = None
        best_confidence = 0.0

        for model in models:
            logger.info(f"Trying model: {model}")

            attempt = await self._extract_with_model(image_bytes, template, model, api_keys)
            model_attempts.append(attempt)

            if not attempt.success:
                logger.warning(f"Model {model} failed: {attempt.error}")
                continue

            # Check if this result meets our threshold
            if attempt.total_confidence >= self.confidence_threshold and \
               attempt.completeness >= 0.90:
                logger.info(f"Model {model} met confidence threshold, stopping sequential extraction")
                best_result = attempt
                break

            # Track best result
            if attempt.total_confidence > best_confidence:
                best_confidence = attempt.total_confidence
                best_result = attempt

        if best_result is None:
            # All models failed
            return self._create_failed_result(model_attempts, models)

        # Check if we should retry low-confidence fields with other models
        if best_result.completeness < 1.0 or best_result.total_confidence < self.confidence_threshold:
            logger.info("Retrying missing/low-confidence fields with other models")
            best_result = await self._retry_fields(
                image_bytes, template, best_result, models, api_keys, model_attempts
            )

        return self._create_result_from_attempts([best_result] + model_attempts, models, template)

    async def _extract_parallel(
        self,
        image_bytes: bytes,
        template: Dict[str, Any],
        models: List[VisionModel],
        api_keys: Dict[str, str]
    ) -> MultiModelExtractionResult:
        """
        Parallel extraction: Run all models simultaneously and pick best results per field.
        """
        logger.info(f"Running parallel extraction with {len(models)} models")

        # Run all models in parallel
        tasks = [
            self._extract_with_model(image_bytes, template, model, api_keys)
            for model in models
        ]

        model_attempts = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed attempts
        successful_attempts = [
            attempt for attempt in model_attempts
            if isinstance(attempt, ModelAttempt) and attempt.success
        ]

        if not successful_attempts:
            return self._create_failed_result(model_attempts, models)

        # Combine results: pick best extraction for each field
        return self._combine_parallel_results(successful_attempts, models, template)

    async def _extract_hybrid(
        self,
        image_bytes: bytes,
        template: Dict[str, Any],
        models: List[VisionModel],
        api_keys: Dict[str, str]
    ) -> MultiModelExtractionResult:
        """
        Hybrid extraction: Try primary model first, then parallel for low-confidence fields.
        """
        logger.info("Starting hybrid extraction")

        # First, try primary model (first in list)
        primary_model = models[0]
        primary_attempt = await self._extract_with_model(
            image_bytes, template, primary_model, api_keys
        )

        model_attempts = [primary_attempt]

        if not primary_attempt.success:
            # Primary failed, fall back to parallel with remaining models
            logger.warning(f"Primary model {primary_model} failed, falling back to parallel")
            return await self._extract_parallel(image_bytes, template, models[1:], api_keys)

        # Check for missing or low-confidence fields
        fields_to_retry = set()

        for field_name in template.get('fields', []):
            field_name_key = field_name['name']
            if field_name_key in primary_attempt.fields_missing:
                fields_to_retry.add(field_name_key)
            elif primary_attempt.field_confidences.get(field_name_key, 0) < self.field_confidence_threshold:
                fields_to_retry.add(field_name_key)

        if fields_to_retry:
            logger.info(f"Retrying {len(fields_to_retry)} fields in parallel with other models")

            # Run other models in parallel for problematic fields
            remaining_models = models[1:]
            tasks = [
                self._extract_with_model(image_bytes, template, model, api_keys)
                for model in remaining_models
            ]

            additional_attempts = await asyncio.gather(*tasks, return_exceptions=True)
            successful_additional = [
                a for a in additional_attempts
                if isinstance(a, ModelAttempt) and a.success
            ]

            model_attempts.extend(successful_additional)

            # Combine primary with best alternatives for problematic fields
            return self._combine_results_for_fields(
                primary_attempt, successful_additional, fields_to_retry, models, template
            )

        # Primary model was good enough
        return self._create_result_from_attempts([primary_attempt], models, template)

    async def _extract_with_model(
        self,
        image_bytes: bytes,
        template: Dict[str, Any],
        model: VisionModel,
        api_keys: Dict[str, str]
    ) -> ModelAttempt:
        """Extract fields using a single model and return attempt details."""
        import time
        start_time = time.time()

        try:
            # Call the extraction service
            result = await self.extraction_service.extract_fields(
                image_bytes=image_bytes,
                template=template,
                model=model,
                api_keys=api_keys
            )

            extraction_time = int((time.time() - start_time) * 1000)

            # Calculate metrics
            extracted_fields = result.get('fields', {})
            field_confidences = result.get('field_confidences', {})

            required_fields = [f['name'] for f in template.get('fields', []) if f.get('required', False)]
            total_fields = [f['name'] for f in template.get('fields', [])]

            fields_missing = [
                f for f in total_fields
                if f not in extracted_fields or extracted_fields[f] is None
            ]

            completeness = 1.0 - (len(fields_missing) / len(total_fields)) if total_fields else 1.0
            avg_confidence = sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0.0

            return ModelAttempt(
                model=model,
                fields_extracted=extracted_fields,
                field_confidences=field_confidences,
                total_confidence=avg_confidence,
                completeness=completeness,
                fields_missing=fields_missing,
                extraction_time_ms=extraction_time,
                success=True
            )

        except Exception as e:
            logger.error(f"Model {model} extraction failed: {e}")
            extraction_time = int((time.time() - start_time) * 1000)

            return ModelAttempt(
                model=model,
                fields_extracted={},
                field_confidences={},
                total_confidence=0.0,
                completeness=0.0,
                fields_missing=[f['name'] for f in template.get('fields', [])],
                extraction_time_ms=extraction_time,
                success=False,
                error=str(e)
            )

    async def _retry_fields(
        self,
        image_bytes: bytes,
        template: Dict[str, Any],
        primary_attempt: ModelAttempt,
        all_models: List[VisionModel],
        api_keys: Dict[str, str],
        existing_attempts: List[ModelAttempt]
    ) -> ModelAttempt:
        """Retry specific fields with other models."""
        # Identify fields that need retry
        fields_to_retry = set()

        for field_def in template.get('fields', []):
            field_name = field_def['name']
            if field_name in primary_attempt.fields_missing:
                fields_to_retry.add(field_name)
            elif primary_attempt.field_confidences.get(field_name, 0) < self.field_confidence_threshold:
                fields_to_retry.add(field_name)

        if not fields_to_retry:
            return primary_attempt

        logger.info(f"Retrying {len(fields_to_retry)} fields: {fields_to_retry}")

        # Find models we haven't tried yet
        tried_models = {attempt.model for attempt in existing_attempts if attempt.success}
        remaining_models = [m for m in all_models if m not in tried_models]

        if not remaining_models:
            logger.info("No remaining models to try for field retry")
            return primary_attempt

        # Try remaining models
        retry_tasks = [
            self._extract_with_model(image_bytes, template, model, api_keys)
            for model in remaining_models
        ]

        retry_attempts = await asyncio.gather(*retry_tasks, return_exceptions=True)

        # Filter successful attempts
        successful_retries = [
            attempt for attempt in retry_attempts
            if isinstance(attempt, ModelAttempt) and attempt.success
        ]

        if not successful_retries:
            logger.info("All retry attempts failed")
            return primary_attempt

        # Update primary attempt with better field values
        updated_fields = primary_attempt.fields_extracted.copy()
        updated_confidences = primary_attempt.field_confidences.copy()

        for field_name in fields_to_retry:
            best_value = None
            best_confidence = primary_attempt.field_confidences.get(field_name, 0.0)

            for retry_attempt in successful_retries:
                if field_name in retry_attempt.fields_extracted:
                    value = retry_attempt.fields_extracted[field_name]
                    confidence = retry_attempt.field_confidences.get(field_name, 0.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_value = value

            if best_value is not None:
                updated_fields[field_name] = best_value
                updated_confidences[field_name] = best_confidence
                logger.info(f"Improved field '{field_name}' with confidence {best_confidence:.2%}")

        # Recalculate metrics
        total_fields = [f['name'] for f in template.get('fields', [])]
        updated_missing = [
            f for f in total_fields
            if f not in updated_fields or updated_fields[f] is None
        ]

        updated_completeness = 1.0 - (len(updated_missing) / len(total_fields)) if total_fields else 1.0
        updated_avg_confidence = sum(updated_confidences.values()) / len(updated_confidences) if updated_confidences else 0.0

        return ModelAttempt(
            model=primary_attempt.model,
            fields_extracted=updated_fields,
            field_confidences=updated_confidences,
            total_confidence=updated_avg_confidence,
            completeness=updated_completeness,
            fields_missing=updated_missing,
            extraction_time_ms=primary_attempt.extraction_time_ms,
            success=True
        )

    def _combine_parallel_results(
        self,
        attempts: List[ModelAttempt],
        models: List[VisionModel],
        template: Dict[str, Any]
    ) -> MultiModelExtractionResult:
        """
        Combine results from parallel extraction:
        For each field, pick the value with highest confidence.
        """
        field_model_map = {}
        extracted_fields = {}
        field_confidences = {}

        # For each field in template, find best extraction across all models
        for field_def in template.get('fields', []):
            field_name = field_def['name']
            best_value = None
            best_confidence = 0.0
            best_model = None

            for attempt in attempts:
                if field_name in attempt.fields_extracted:
                    value = attempt.fields_extracted[field_name]
                    confidence = attempt.field_confidences.get(field_name, 0.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_value = value
                        best_model = attempt.model

            if best_value is not None:
                extracted_fields[field_name] = best_value
                field_confidences[field_name] = best_confidence
                field_model_map[field_name] = best_model

        # Calculate metrics
        total_fields = len(template.get('fields', []))
        missing_fields = [
            f['name'] for f in template.get('fields', [])
            if f['name'] not in extracted_fields
        ]

        low_confidence_fields = [
            f for f, conf in field_confidences.items()
            if conf < self.field_confidence_threshold
        ]

        overall_confidence = sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0.0
        overall_completeness = len(extracted_fields) / total_fields if total_fields else 1.0

        return MultiModelExtractionResult(
            extracted_fields=extracted_fields,
            field_model_map=field_model_map,
            field_confidences=field_confidences,
            model_attempts=attempts,
            missing_fields=missing_fields,
            low_confidence_fields=low_confidence_fields,
            overall_confidence=overall_confidence,
            overall_completeness=overall_completeness,
            models_tried=[a.model for a in attempts],
            extraction_summary="",  # Will be filled later
            field_extraction_notes={},  # Will be filled later
            strategy=ModelStrategy.PARALLEL,
            total_time_ms=0  # Will be filled later
        )

    def _combine_results_for_fields(
        self,
        primary: ModelAttempt,
        alternatives: List[ModelAttempt],
        fields_to_replace: Set[str],
        models: List[VisionModel],
        template: Dict[str, Any]
    ) -> MultiModelExtractionResult:
        """Combine primary results with alternative models for specific fields."""
        # Start with primary results
        extracted_fields = primary.fields_extracted.copy()
        field_confidences = primary.field_confidences.copy()
        field_model_map = {f: primary.model for f in extracted_fields.keys()}

        # Replace specified fields with better alternatives
        for field_name in fields_to_replace:
            best_value = None
            best_confidence = 0.0
            best_model = None

            for attempt in alternatives:
                if field_name in attempt.fields_extracted:
                    value = attempt.fields_extracted[field_name]
                    confidence = attempt.field_confidences.get(field_name, 0.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_value = value
                        best_model = attempt.model

            if best_value is not None and best_confidence > field_confidences.get(field_name, 0):
                extracted_fields[field_name] = best_value
                field_confidences[field_name] = best_confidence
                field_model_map[field_name] = best_model

        # Calculate final metrics
        all_attempts = [primary] + alternatives
        total_fields = len(template.get('fields', []))
        missing_fields = [
            f['name'] for f in template.get('fields', [])
            if f['name'] not in extracted_fields
        ]

        low_confidence_fields = [
            f for f, conf in field_confidences.items()
            if conf < self.field_confidence_threshold
        ]

        overall_confidence = sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0.0
        overall_completeness = len(extracted_fields) / total_fields if total_fields else 1.0

        return MultiModelExtractionResult(
            extracted_fields=extracted_fields,
            field_model_map=field_model_map,
            field_confidences=field_confidences,
            model_attempts=all_attempts,
            missing_fields=missing_fields,
            low_confidence_fields=low_confidence_fields,
            overall_confidence=overall_confidence,
            overall_completeness=overall_completeness,
            models_tried=[a.model for a in all_attempts],
            extraction_summary="",
            field_extraction_notes={},
            strategy=ModelStrategy.HYBRID,
            total_time_ms=0
        )

    def _create_result_from_attempts(
        self,
        attempts: List[ModelAttempt],
        models: List[VisionModel],
        template: Dict[str, Any]
    ) -> MultiModelExtractionResult:
        """Create result from list of attempts (typically just one for sequential)."""
        best_attempt = attempts[0] if attempts else None

        if not best_attempt or not best_attempt.success:
            return self._create_failed_result(attempts, models)

        field_model_map = {f: best_attempt.model for f in best_attempt.fields_extracted.keys()}

        low_confidence_fields = [
            f for f, conf in best_attempt.field_confidences.items()
            if conf < self.field_confidence_threshold
        ]

        return MultiModelExtractionResult(
            extracted_fields=best_attempt.fields_extracted,
            field_model_map=field_model_map,
            field_confidences=best_attempt.field_confidences,
            model_attempts=attempts,
            missing_fields=best_attempt.fields_missing,
            low_confidence_fields=low_confidence_fields,
            overall_confidence=best_attempt.total_confidence,
            overall_completeness=best_attempt.completeness,
            models_tried=[a.model for a in attempts],
            extraction_summary="",
            field_extraction_notes={},
            strategy=ModelStrategy.SEQUENTIAL,
            total_time_ms=0
        )

    def _create_failed_result(
        self,
        attempts: List[ModelAttempt],
        models: List[VisionModel]
    ) -> MultiModelExtractionResult:
        """Create result when all models failed."""
        return MultiModelExtractionResult(
            extracted_fields={},
            field_model_map={},
            field_confidences={},
            model_attempts=attempts if isinstance(attempts, list) else [],
            missing_fields=[],
            low_confidence_fields=[],
            overall_confidence=0.0,
            overall_completeness=0.0,
            models_tried=[m for m in models],
            extraction_summary="All models failed to extract document",
            field_extraction_notes={},
            strategy=ModelStrategy.SEQUENTIAL,
            total_time_ms=0
        )

    def _generate_summary(
        self,
        result: MultiModelExtractionResult,
        template: Dict[str, Any]
    ) -> str:
        """Generate user-friendly summary of extraction attempts."""
        models_tried = ", ".join(result.models_tried)

        if result.overall_completeness == 1.0 and result.overall_confidence >= self.confidence_threshold:
            return (f"✓ Successfully extracted all fields using {len(result.models_tried)} model(s): {models_tried}. "
                   f"Average confidence: {result.overall_confidence:.1%}")

        elif result.overall_completeness >= 0.70:
            missing_count = len(result.missing_fields)
            low_conf_count = len(result.low_confidence_fields)

            parts = []
            if missing_count > 0:
                parts.append(f"{missing_count} field(s) could not be extracted")
            if low_conf_count > 0:
                parts.append(f"{low_conf_count} field(s) have low confidence")

            issues = " and ".join(parts)

            return (f"⚠ Partial extraction: {issues}. "
                   f"Tried {len(result.models_tried)} model(s): {models_tried}. "
                   f"Completeness: {result.overall_completeness:.1%}, "
                   f"Confidence: {result.overall_confidence:.1%}")

        else:
            return (f"✗ Extraction failed or incomplete. "
                   f"Tried {len(result.models_tried)} model(s): {models_tried}, "
                   f"but could only extract {result.overall_completeness:.1%} of fields.")

    def _generate_field_notes(
        self,
        result: MultiModelExtractionResult,
        template: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate per-field notes about extraction."""
        notes = {}

        for field_def in template.get('fields', []):
            field_name = field_def['name']

            if field_name in result.missing_fields:
                models_str = ", ".join(result.models_tried)
                notes[field_name] = f"Could not be extracted even after trying: {models_str}"

            elif field_name in result.low_confidence_fields:
                conf = result.field_confidences[field_name]
                model = result.field_model_map[field_name]
                notes[field_name] = f"Low confidence ({conf:.1%}) - extracted by {model}. Please verify."

            elif field_name in result.extracted_fields:
                model = result.field_model_map[field_name]
                conf = result.field_confidences[field_name]
                notes[field_name] = f"Extracted by {model} with {conf:.1%} confidence"

        return notes
