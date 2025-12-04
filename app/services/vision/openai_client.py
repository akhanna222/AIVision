"""
OpenAI GPT-4o Vision model client.
Supports GPT-4o, GPT-4o-mini, and GPT-4-Vision models.
"""

import json
import logging
from typing import Dict, List
from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APITimeoutError

from .base_client import (
    BaseVisionClient,
    VisionModelError,
    VisionModelAPIError,
    VisionModelRateLimitError,
    VisionModelTimeoutError
)

logger = logging.getLogger(__name__)


class OpenAIClient(BaseVisionClient):
    """OpenAI vision model client"""

    # Model pricing (USD per 1M tokens)
    PRICING = {
        "gpt-4o": {
            "input": 2.50,
            "output": 10.00
        },
        "gpt-4o-mini": {
            "input": 0.15,
            "output": 0.60
        },
        "gpt-4-vision-preview": {
            "input": 10.00,
            "output": 30.00
        }
    }

    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        super().__init__(api_key)
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key=api_key)

        logger.info(f"Initialized OpenAI client with model: {model_name}")

    async def extract(
        self,
        image_bytes: bytes,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096
    ) -> Dict:
        """
        Extract data from image using OpenAI vision model.

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

            # Create message with image
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert document data extraction system. Extract information with high precision and return structured JSON output."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]

            # Call API
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Add usage metadata
            if response.usage:
                result['_metadata'] = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }

            logger.info(
                f"OpenAI extraction successful. Model: {self.model_name}, "
                f"Tokens: {result.get('_metadata', {}).get('total_tokens', 'unknown')}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            raise VisionModelError(f"Invalid JSON response from OpenAI: {str(e)}")

        except RateLimitError as e:
            logger.error("OpenAI rate limit exceeded")
            raise VisionModelRateLimitError(f"OpenAI rate limit exceeded: {str(e)}")

        except APITimeoutError as e:
            logger.error("OpenAI API timeout")
            raise VisionModelTimeoutError(f"OpenAI timeout: {str(e)}")

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise VisionModelAPIError(f"OpenAI API error: {str(e)}", status_code=e.status_code if hasattr(e, 'status_code') else None)

        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            raise VisionModelError(f"OpenAI extraction failed: {str(e)}")

    async def classify_document(
        self,
        image_bytes: bytes,
        categories: List[str]
    ) -> Dict[str, float]:
        """
        Classify document type using OpenAI.

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
}}"""

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
            logger.error(f"OpenAI classification failed: {e}")
            raise VisionModelError(f"Classification failed: {str(e)}")

    def estimate_cost(
        self,
        num_images: int,
        tokens_per_image: int = 1000
    ) -> float:
        """
        Estimate extraction cost for OpenAI.

        Args:
            num_images: Number of images to process
            tokens_per_image: Estimated output tokens per image

        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(self.model_name, self.PRICING["gpt-4o"])

        # Estimate: 1 high-detail image ≈ 765 tokens (for 2048x2048)
        # Smaller images use fewer tokens
        # Prompt ≈ 500 tokens
        input_tokens = num_images * (765 + 500)
        output_tokens = num_images * tokens_per_image

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    async def extract_with_structured_output(
        self,
        image_bytes: bytes,
        schema: Dict,
        prompt: str,
        temperature: float = 0.0
    ) -> Dict:
        """
        Extract data with structured output schema (OpenAI-specific feature).

        Args:
            image_bytes: Image data as bytes
            schema: JSON schema for output structure
            prompt: Extraction prompt
            temperature: Model temperature

        Returns:
            Dict conforming to schema
        """
        try:
            # Validate image
            if not self.validate_image(image_bytes):
                raise VisionModelError("Invalid image data")

            # Encode image
            image_base64 = self.encode_image_to_base64(image_bytes)

            # Create message
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert document data extraction system."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]

            # Call API with structured output
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "extraction_result",
                        "schema": schema
                    }
                }
            )

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            logger.info("OpenAI structured extraction successful")
            return result

        except Exception as e:
            logger.error(f"OpenAI structured extraction failed: {e}")
            raise VisionModelError(f"Structured extraction failed: {str(e)}")
