"""
Tests for Multi-Model Extraction Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.multi_model_extractor import (
    MultiModelExtractor,
    ModelStrategy,
    ModelAttempt,
    MultiModelExtractionResult
)
from app.services.vision.base import VisionModel


@pytest.fixture
def mock_extraction_service():
    """Mock extraction service"""
    service = MagicMock()
    service.extract_fields = AsyncMock()
    return service


@pytest.fixture
def sample_template():
    """Sample template for testing"""
    return {
        "template_id": "test_template",
        "template_name": "Test Template",
        "category": "invoice",
        "fields": [
            {"name": "invoice_number", "type": "string", "required": True},
            {"name": "date", "type": "date", "required": True},
            {"name": "total", "type": "number", "required": True},
            {"name": "vendor", "type": "string", "required": False}
        ]
    }


@pytest.fixture
def sample_image_bytes():
    """Sample image bytes"""
    return b"fake_image_data"


@pytest.fixture
def api_keys():
    """Sample API keys"""
    return {
        "gemini": "test_gemini_key",
        "openai": "test_openai_key",
        "anthropic": "test_anthropic_key"
    }


class TestMultiModelExtractor:
    """Test MultiModelExtractor class"""

    def test_initialization(self, mock_extraction_service):
        """Test extractor initialization"""
        extractor = MultiModelExtractor(
            extraction_service=mock_extraction_service,
            default_strategy=ModelStrategy.SEQUENTIAL,
            confidence_threshold=0.85,
            field_confidence_threshold=0.75,
            max_models_to_try=3
        )

        assert extractor.extraction_service == mock_extraction_service
        assert extractor.default_strategy == ModelStrategy.SEQUENTIAL
        assert extractor.confidence_threshold == 0.85
        assert extractor.field_confidence_threshold == 0.75
        assert extractor.max_models_to_try == 3

    @pytest.mark.asyncio
    async def test_sequential_strategy_first_model_succeeds(
        self, mock_extraction_service, sample_template, sample_image_bytes, api_keys
    ):
        """Test sequential strategy when first model succeeds"""
        # Mock successful extraction from first model
        mock_extraction_service.extract_fields.return_value = {
            "fields": {
                "invoice_number": "INV-001",
                "date": "2025-12-05",
                "total": 1000.00,
                "vendor": "ACME Corp"
            },
            "field_confidences": {
                "invoice_number": 0.95,
                "date": 0.92,
                "total": 0.98,
                "vendor": 0.90
            }
        }

        extractor = MultiModelExtractor(mock_extraction_service)
        result = await extractor.extract_with_multi_model(
            image_bytes=sample_image_bytes,
            template=sample_template,
            models=[VisionModel.GEMINI_2_FLASH, VisionModel.GPT4O],
            api_keys=api_keys,
            strategy=ModelStrategy.SEQUENTIAL
        )

        # Should only try first model
        assert mock_extraction_service.extract_fields.call_count == 1
        assert result.overall_completeness == 1.0
        assert result.overall_confidence >= 0.90
        assert len(result.models_tried) == 1
        assert result.models_tried[0] == VisionModel.GEMINI_2_FLASH

    @pytest.mark.asyncio
    async def test_sequential_strategy_fallback_to_second_model(
        self, mock_extraction_service, sample_template, sample_image_bytes, api_keys
    ):
        """Test sequential strategy falling back to second model"""
        # First model returns low confidence
        # Second model returns high confidence
        mock_extraction_service.extract_fields.side_effect = [
            {
                "fields": {
                    "invoice_number": "INV-001",
                    "date": "2025-12-05",
                    "total": None,  # Missing field
                    "vendor": "ACME Corp"
                },
                "field_confidences": {
                    "invoice_number": 0.60,
                    "date": 0.65,
                    "vendor": 0.55
                }
            },
            {
                "fields": {
                    "invoice_number": "INV-001",
                    "date": "2025-12-05",
                    "total": 1000.00,
                    "vendor": "ACME Corp"
                },
                "field_confidences": {
                    "invoice_number": 0.95,
                    "date": 0.92,
                    "total": 0.98,
                    "vendor": 0.90
                }
            }
        ]

        extractor = MultiModelExtractor(mock_extraction_service)
        result = await extractor.extract_with_multi_model(
            image_bytes=sample_image_bytes,
            template=sample_template,
            models=[VisionModel.GEMINI_2_FLASH, VisionModel.GPT4O],
            api_keys=api_keys,
            strategy=ModelStrategy.SEQUENTIAL
        )

        # Should try both models
        assert mock_extraction_service.extract_fields.call_count == 2
        assert len(result.models_tried) >= 1

    @pytest.mark.asyncio
    async def test_parallel_strategy(
        self, mock_extraction_service, sample_template, sample_image_bytes, api_keys
    ):
        """Test parallel strategy runs all models"""
        # Different results from different models
        mock_extraction_service.extract_fields.side_effect = [
            # Gemini result
            {
                "fields": {
                    "invoice_number": "INV-001",
                    "date": "2025-12-05",
                    "total": 1000.00,
                    "vendor": "ACME"
                },
                "field_confidences": {
                    "invoice_number": 0.95,
                    "date": 0.85,
                    "total": 0.90,
                    "vendor": 0.75
                }
            },
            # GPT-4 result
            {
                "fields": {
                    "invoice_number": "INV-001",
                    "date": "2025-12-05",
                    "total": 1000.00,
                    "vendor": "ACME Corporation"
                },
                "field_confidences": {
                    "invoice_number": 0.92,
                    "date": 0.95,
                    "total": 0.88,
                    "vendor": 0.98
                }
            }
        ]

        extractor = MultiModelExtractor(mock_extraction_service)
        result = await extractor.extract_with_multi_model(
            image_bytes=sample_image_bytes,
            template=sample_template,
            models=[VisionModel.GEMINI_2_FLASH, VisionModel.GPT4O],
            api_keys=api_keys,
            strategy=ModelStrategy.PARALLEL
        )

        # Should try all models
        assert mock_extraction_service.extract_fields.call_count == 2

        # Should pick best value for each field
        # vendor should be from GPT-4 (0.98 confidence)
        assert result.field_model_map["vendor"] == VisionModel.GPT4O
        # invoice_number should be from Gemini (0.95 confidence)
        assert result.field_model_map["invoice_number"] == VisionModel.GEMINI_2_FLASH

    @pytest.mark.asyncio
    async def test_hybrid_strategy_primary_sufficient(
        self, mock_extraction_service, sample_template, sample_image_bytes, api_keys
    ):
        """Test hybrid strategy when primary model is sufficient"""
        # Primary model returns good results
        mock_extraction_service.extract_fields.return_value = {
            "fields": {
                "invoice_number": "INV-001",
                "date": "2025-12-05",
                "total": 1000.00,
                "vendor": "ACME Corp"
            },
            "field_confidences": {
                "invoice_number": 0.95,
                "date": 0.92,
                "total": 0.98,
                "vendor": 0.90
            }
        }

        extractor = MultiModelExtractor(mock_extraction_service)
        result = await extractor.extract_with_multi_model(
            image_bytes=sample_image_bytes,
            template=sample_template,
            models=[VisionModel.GEMINI_2_FLASH, VisionModel.GPT4O, VisionModel.CLAUDE_SONNET_4],
            api_keys=api_keys,
            strategy=ModelStrategy.HYBRID
        )

        # Should only try primary model
        assert mock_extraction_service.extract_fields.call_count == 1
        assert result.overall_completeness == 1.0

    @pytest.mark.asyncio
    async def test_hybrid_strategy_retry_low_confidence_fields(
        self, mock_extraction_service, sample_template, sample_image_bytes, api_keys
    ):
        """Test hybrid strategy retrying low-confidence fields"""
        # Primary model has low confidence on some fields
        # Secondary models improve those fields
        mock_extraction_service.extract_fields.side_effect = [
            # Primary (Gemini) result
            {
                "fields": {
                    "invoice_number": "INV-001",
                    "date": "2025-12-05",
                    "total": 1000.00,
                    "vendor": "ACME"  # Low confidence
                },
                "field_confidences": {
                    "invoice_number": 0.95,
                    "date": 0.92,
                    "total": 0.98,
                    "vendor": 0.60  # Below threshold
                }
            },
            # GPT-4 result
            {
                "fields": {
                    "invoice_number": "INV-001",
                    "date": "2025-12-05",
                    "total": 1000.00,
                    "vendor": "ACME Corporation"
                },
                "field_confidences": {
                    "invoice_number": 0.90,
                    "date": 0.88,
                    "total": 0.92,
                    "vendor": 0.95  # High confidence
                }
            },
            # Claude result
            {
                "fields": {
                    "invoice_number": "INV-001",
                    "date": "2025-12-05",
                    "total": 1000.00,
                    "vendor": "ACME Corp"
                },
                "field_confidences": {
                    "invoice_number": 0.93,
                    "date": 0.90,
                    "total": 0.95,
                    "vendor": 0.85
                }
            }
        ]

        extractor = MultiModelExtractor(mock_extraction_service)
        result = await extractor.extract_with_multi_model(
            image_bytes=sample_image_bytes,
            template=sample_template,
            models=[VisionModel.GEMINI_2_FLASH, VisionModel.GPT4O, VisionModel.CLAUDE_SONNET_4],
            api_keys=api_keys,
            strategy=ModelStrategy.HYBRID
        )

        # Should try primary + secondary models
        assert mock_extraction_service.extract_fields.call_count == 3

        # vendor field should be improved by GPT-4
        assert result.field_confidences["vendor"] > 0.60

    @pytest.mark.asyncio
    async def test_all_models_fail(
        self, mock_extraction_service, sample_template, sample_image_bytes, api_keys
    ):
        """Test behavior when all models fail"""
        # All models raise exceptions
        mock_extraction_service.extract_fields.side_effect = Exception("API error")

        extractor = MultiModelExtractor(mock_extraction_service)
        result = await extractor.extract_with_multi_model(
            image_bytes=sample_image_bytes,
            template=sample_template,
            models=[VisionModel.GEMINI_2_FLASH, VisionModel.GPT4O],
            api_keys=api_keys,
            strategy=ModelStrategy.SEQUENTIAL
        )

        # Should return failed result
        assert result.overall_completeness == 0.0
        assert result.overall_confidence == 0.0
        assert len(result.extracted_fields) == 0
        assert "failed" in result.extraction_summary.lower()

    @pytest.mark.asyncio
    async def test_partial_field_extraction(
        self, mock_extraction_service, sample_template, sample_image_bytes, api_keys
    ):
        """Test handling of partial field extraction"""
        # Model extracts some but not all fields
        mock_extraction_service.extract_fields.return_value = {
            "fields": {
                "invoice_number": "INV-001",
                "date": "2025-12-05",
                "total": None,  # Missing required field
                "vendor": None   # Missing optional field
            },
            "field_confidences": {
                "invoice_number": 0.95,
                "date": 0.92
            }
        }

        extractor = MultiModelExtractor(mock_extraction_service)
        result = await extractor.extract_with_multi_model(
            image_bytes=sample_image_bytes,
            template=sample_template,
            models=[VisionModel.GEMINI_2_FLASH],
            api_keys=api_keys,
            strategy=ModelStrategy.SEQUENTIAL
        )

        # Should identify missing fields
        assert "total" in result.missing_fields
        assert "vendor" in result.missing_fields
        assert result.overall_completeness < 1.0
        assert len(result.missing_fields) == 2

    def test_generate_summary_complete_success(self, mock_extraction_service, sample_template):
        """Test summary generation for complete successful extraction"""
        extractor = MultiModelExtractor(mock_extraction_service)

        result = MultiModelExtractionResult(
            extracted_fields={"field1": "value1", "field2": "value2"},
            field_model_map={"field1": "gemini", "field2": "gemini"},
            field_confidences={"field1": 0.95, "field2": 0.92},
            model_attempts=[],
            missing_fields=[],
            low_confidence_fields=[],
            overall_confidence=0.935,
            overall_completeness=1.0,
            models_tried=["gemini-2.0-flash-exp"],
            extraction_summary="",
            field_extraction_notes={},
            strategy=ModelStrategy.SEQUENTIAL,
            total_time_ms=1000
        )

        summary = extractor._generate_summary(result, sample_template)

        assert "✓" in summary or "success" in summary.lower()
        assert "gemini" in summary.lower()
        assert "93" in summary or "0.93" in summary  # Confidence percentage

    def test_generate_summary_partial_extraction(self, mock_extraction_service, sample_template):
        """Test summary generation for partial extraction"""
        extractor = MultiModelExtractor(mock_extraction_service)

        result = MultiModelExtractionResult(
            extracted_fields={"field1": "value1"},
            field_model_map={"field1": "gemini"},
            field_confidences={"field1": 0.75},
            model_attempts=[],
            missing_fields=["field2", "field3"],
            low_confidence_fields=["field4"],
            overall_confidence=0.75,
            overall_completeness=0.75,
            models_tried=["gemini-2.0-flash-exp", "gpt-4o"],
            extraction_summary="",
            field_extraction_notes={},
            strategy=ModelStrategy.SEQUENTIAL,
            total_time_ms=2000
        )

        summary = extractor._generate_summary(result, sample_template)

        assert "⚠" in summary or "partial" in summary.lower()
        assert "2" in summary  # Missing fields count
        assert "1" in summary  # Low confidence count

    def test_generate_field_notes(self, mock_extraction_service, sample_template):
        """Test field notes generation"""
        extractor = MultiModelExtractor(mock_extraction_service)

        result = MultiModelExtractionResult(
            extracted_fields={"invoice_number": "INV-001", "date": "2025-12-05"},
            field_model_map={"invoice_number": "gemini-2.0-flash-exp", "date": "gpt-4o"},
            field_confidences={"invoice_number": 0.95, "date": 0.65},
            model_attempts=[],
            missing_fields=["total"],
            low_confidence_fields=["date"],
            overall_confidence=0.80,
            overall_completeness=0.75,
            models_tried=["gemini-2.0-flash-exp", "gpt-4o"],
            extraction_summary="",
            field_extraction_notes={},
            strategy=ModelStrategy.PARALLEL,
            total_time_ms=1500
        )

        notes = extractor._generate_field_notes(result, sample_template)

        # Check notes for missing field
        assert "total" in notes
        assert "could not be extracted" in notes["total"].lower()

        # Check notes for low confidence field
        assert "date" in notes
        assert "low confidence" in notes["date"].lower()

        # Check notes for successful field
        assert "invoice_number" in notes
        assert "gemini" in notes["invoice_number"].lower()


@pytest.mark.asyncio
async def test_max_models_limit(mock_extraction_service, sample_template, sample_image_bytes, api_keys):
    """Test that max_models_to_try is respected"""
    mock_extraction_service.extract_fields.return_value = {
        "fields": {"invoice_number": "INV-001"},
        "field_confidences": {"invoice_number": 0.60}  # Low confidence
    }

    extractor = MultiModelExtractor(mock_extraction_service, max_models_to_try=2)

    # Provide 5 models but only 2 should be tried
    result = await extractor.extract_with_multi_model(
        image_bytes=sample_image_bytes,
        template=sample_template,
        models=[
            VisionModel.GEMINI_2_FLASH,
            VisionModel.GPT4O,
            VisionModel.CLAUDE_SONNET_4,
            VisionModel.GEMINI_2_FLASH,
            VisionModel.GPT4O
        ],
        api_keys=api_keys,
        strategy=ModelStrategy.SEQUENTIAL
    )

    # Should not exceed max_models_to_try
    assert len(result.models_tried) <= 2
