"""
Anthropic Claude vision model client.
Supports Claude Sonnet 4 and Claude Opus 4 models.
"""

import json
import logging
from typing import Dict, List
from anthropic import AsyncAnthropic, APIError, RateLimitError, APITimeoutError

from .base_client import (
    BaseVisionClient,
    VisionModelError,
    VisionModelAPIError,
    VisionModelRateLimitError,
    VisionModelTimeoutError
)

logger = logging.getLogger(__name__)


class AnthropicClient(BaseVisionClient):
    """Anthropic Claude vision model client"""

    # Model pricing (USD per 1M tokens)
    PRICING = {
        "claude-sonnet-4-20250514": {
            "input": 3.00,
            "output": 15.00
        },
        "claude-opus-4-20250514": {
            "input": 15.00,
            "output": 75.00
        }
    }

    def __init__(self, api_key: str, model_name: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key)
        self.model_name = model_name
        self.client = AsyncAnthropic(api_key=api_key)

        logger.info(f"Initialized Anthropic client with model: {model_name}")

    async def extract(
        self,
        image_bytes: bytes,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096
    ) -> Dict:
        """
        Extract data from image using Claude vision model.

        Args:
            image_bytes: Image data as bytes
            prompt: Extraction prompt with field definitions
            temperature: Model temperature (0.0 = deterministic)
            max_tokens: Maximum response tokens

        Returns:
            Dict containing extracted fields

        Raises:
            VisionModelError: If extraction fails
        """
        try:
            # Validate image
            if not self.validate_image(image_bytes):
                raise VisionModelError("Invalid image data")

            # Encode image to base64
            image_base64 = self.encode_image_to_base64(image_bytes)

            # Detect image media type
            from PIL import Image
            from io import BytesIO
            image = Image.open(BytesIO(image_bytes))
            media_type = f"image/{image.format.lower()}" if image.format else "image/jpeg"

            # Create message with image
            message = await self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are an expert document data extraction system. Extract information with high precision and return structured JSON output. Return ONLY valid JSON with no additional commentary.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Extract text response
            content = message.content[0].text

            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = content.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                result = json.loads(text.strip())

            # Add usage metadata
            if message.usage:
                result['_metadata'] = {
                    'prompt_tokens': message.usage.input_tokens,
                    'completion_tokens': message.usage.output_tokens,
                    'total_tokens': message.usage.input_tokens + message.usage.output_tokens
                }

            logger.info(
                f"Claude extraction successful. Model: {self.model_name}, "
                f"Tokens: {result.get('_metadata', {}).get('total_tokens', 'unknown')}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            raise VisionModelError(f"Invalid JSON response from Claude: {str(e)}")

        except RateLimitError as e:
            logger.error("Claude rate limit exceeded")
            raise VisionModelRateLimitError(f"Claude rate limit exceeded: {str(e)}")

        except APITimeoutError as e:
            logger.error("Claude API timeout")
            raise VisionModelTimeoutError(f"Claude timeout: {str(e)}")

        except APIError as e:
            logger.error(f"Claude API error: {e}")
            status_code = e.status_code if hasattr(e, 'status_code') else None
            raise VisionModelAPIError(f"Claude API error: {str(e)}", status_code=status_code)

        except Exception as e:
            logger.error(f"Claude extraction failed: {e}")
            raise VisionModelError(f"Claude extraction failed: {str(e)}")

    async def classify_document(
        self,
        image_bytes: bytes,
        categories: List[str]
    ) -> Dict[str, float]:
        """
        Classify document type using Claude.

        Args:
            image_bytes: Image data as bytes
            categories: List of possible document categories

        Returns:
            Dict mapping category names to confidence scores
        """
        try:
            categories_str = "\n".join([f"- {cat}" for cat in categories])

            prompt = f"""Analyze this document image and classify it into one of these categories:

{categories_str}

Return a JSON object with confidence scores for each category (0.0 to 1.0).
The scores should sum to approximately 1.0.

Example format:
{{
  "mortgage_application": 0.85,
  "bank_statement": 0.10,
  "passport": 0.05
}}

Return ONLY the JSON object."""

            result = await self.extract(
                image_bytes=image_bytes,
                prompt=prompt,
                temperature=0.0,
                max_tokens=512
            )

            # Remove metadata if present
            if '_metadata' in result:
                del result['_metadata']

            return result

        except Exception as e:
            logger.error(f"Claude classification failed: {e}")
            raise VisionModelError(f"Classification failed: {str(e)}")

    def estimate_cost(
        self,
        num_images: int,
        tokens_per_image: int = 1000
    ) -> float:
        """
        Estimate extraction cost for Claude.

        Args:
            num_images: Number of images to process
            tokens_per_image: Estimated output tokens per image

        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(self.model_name, self.PRICING["claude-sonnet-4-20250514"])

        # Estimate: Claude image tokens vary by size
        # For a typical document scan: ~1600 tokens
        # Prompt ≈ 500 tokens
        input_tokens = num_images * (1600 + 500)
        output_tokens = num_images * tokens_per_image

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    async def extract_with_pdf(
        self,
        pdf_bytes: bytes,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 8192
    ) -> Dict:
        """
        Extract data from PDF using Claude (supports PDF documents directly).

        Args:
            pdf_bytes: PDF file bytes
            prompt: Extraction prompt
            temperature: Model temperature
            max_tokens: Maximum response tokens

        Returns:
            Dict containing extracted fields
        """
        try:
            # Encode PDF to base64
            import base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

            # Create message with PDF
            message = await self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are an expert document data extraction system. Extract information with high precision and return structured JSON output.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Extract and parse response
            content = message.content[0].text
            result = json.loads(content)

            logger.info("Claude PDF extraction successful")
            return result

        except Exception as e:
            logger.error(f"Claude PDF extraction failed: {e}")
            raise VisionModelError(f"PDF extraction failed: {str(e)}")

    def supports_pdf(self) -> bool:
        """Check if model supports direct PDF input"""
        return True  # Claude 3+ supports PDFs
