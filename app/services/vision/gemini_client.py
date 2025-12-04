"""
Google Gemini vision model client.
Supports Gemini 2.0 Flash and Gemini 2.5 Pro models.
"""

import json
import logging
from typing import Dict, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base_client import (
    BaseVisionClient,
    VisionModelError,
    VisionModelAPIError,
    VisionModelRateLimitError
)

logger = logging.getLogger(__name__)


class GeminiClient(BaseVisionClient):
    """Google Gemini vision model client"""

    # Model pricing (USD per 1M tokens)
    PRICING = {
        "gemini-2.0-flash-exp": {
            "input": 0.10,  # $0.10 per 1M input tokens
            "output": 0.40  # $0.40 per 1M output tokens
        },
        "gemini-2.5-pro-preview": {
            "input": 1.25,
            "output": 5.00
        }
    }

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(api_key)
        self.model_name = model_name

        # Configure API
        genai.configure(api_key=api_key)

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        logger.info(f"Initialized Gemini client with model: {model_name}")

    async def extract(
        self,
        image_bytes: bytes,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096
    ) -> Dict:
        """
        Extract data from image using Gemini vision model.

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

            # Prepare image
            from PIL import Image
            from io import BytesIO
            image = Image.open(BytesIO(image_bytes))

            # Generate content
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json"
            )

            response = self.model.generate_content(
                [prompt, image],
                generation_config=generation_config
            )

            # Parse response
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                result = json.loads(text.strip())

            # Add usage metadata
            if hasattr(response, 'usage_metadata'):
                result['_metadata'] = {
                    'prompt_tokens': response.usage_metadata.prompt_token_count,
                    'completion_tokens': response.usage_metadata.candidates_token_count,
                    'total_tokens': response.usage_metadata.total_token_count
                }

            logger.info(
                f"Gemini extraction successful. Tokens: {result.get('_metadata', {}).get('total_tokens', 'unknown')}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            raise VisionModelError(f"Invalid JSON response from Gemini: {str(e)}")

        except Exception as e:
            error_msg = str(e).lower()

            if "429" in error_msg or "rate limit" in error_msg:
                logger.error("Gemini rate limit exceeded")
                raise VisionModelRateLimitError("Gemini rate limit exceeded")

            if "quota" in error_msg:
                logger.error("Gemini quota exceeded")
                raise VisionModelAPIError("Gemini quota exceeded", status_code=429)

            logger.error(f"Gemini extraction failed: {e}")
            raise VisionModelError(f"Gemini extraction failed: {str(e)}")

    async def classify_document(
        self,
        image_bytes: bytes,
        categories: List[str]
    ) -> Dict[str, float]:
        """
        Classify document type using Gemini.

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

Return ONLY the JSON object, no additional text."""

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
            logger.error(f"Gemini classification failed: {e}")
            raise VisionModelError(f"Classification failed: {str(e)}")

    def estimate_cost(
        self,
        num_images: int,
        tokens_per_image: int = 1000
    ) -> float:
        """
        Estimate extraction cost for Gemini.

        Args:
            num_images: Number of images to process
            tokens_per_image: Estimated tokens per image

        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(self.model_name, self.PRICING["gemini-2.0-flash-exp"])

        # Estimate: 1 image ≈ 258 tokens, prompt ≈ 500 tokens, response ≈ 500 tokens
        input_tokens = num_images * (258 + 500)  # Image + prompt
        output_tokens = num_images * tokens_per_image

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def supports_pdf(self) -> bool:
        """Check if model supports direct PDF input"""
        return True  # Gemini 2.0+ supports PDF

    async def extract_from_pdf(
        self,
        pdf_bytes: bytes,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 8192
    ) -> Dict:
        """
        Extract data directly from PDF using Gemini (2.0+ feature).

        Args:
            pdf_bytes: PDF file bytes
            prompt: Extraction prompt
            temperature: Model temperature
            max_tokens: Maximum response tokens

        Returns:
            Dict containing extracted fields
        """
        try:
            # Upload PDF to Gemini
            import tempfile
            import os

            # Gemini requires file upload for PDFs
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_path = tmp_file.name

            try:
                # Upload file
                uploaded_file = genai.upload_file(tmp_path)

                # Generate content
                generation_config = genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json"
                )

                response = self.model.generate_content(
                    [prompt, uploaded_file],
                    generation_config=generation_config
                )

                # Parse response
                result = json.loads(response.text)

                logger.info("Gemini PDF extraction successful")
                return result

            finally:
                # Clean up temp file
                os.unlink(tmp_path)
                # Delete uploaded file
                try:
                    genai.delete_file(uploaded_file.name)
                except:
                    pass

        except Exception as e:
            logger.error(f"Gemini PDF extraction failed: {e}")
            raise VisionModelError(f"PDF extraction failed: {str(e)}")
