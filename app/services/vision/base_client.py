"""
Base vision model client interface.
All vision model clients should implement this interface for consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import base64
from io import BytesIO
from PIL import Image


class BaseVisionClient(ABC):
    """Abstract base class for vision model clients"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def extract(
        self,
        image_bytes: bytes,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096
    ) -> Dict:
        """
        Extract data from image using vision model.

        Args:
            image_bytes: Image data as bytes
            prompt: Extraction prompt with field definitions
            temperature: Model temperature (0.0 = deterministic)
            max_tokens: Maximum response tokens

        Returns:
            Dict containing extracted fields and metadata

        Raises:
            VisionModelError: If extraction fails
        """
        pass

    @abstractmethod
    async def classify_document(
        self,
        image_bytes: bytes,
        categories: List[str]
    ) -> Dict[str, float]:
        """
        Classify document type.

        Args:
            image_bytes: Image data as bytes
            categories: List of possible document categories

        Returns:
            Dict mapping category names to confidence scores

        Raises:
            VisionModelError: If classification fails
        """
        pass

    @staticmethod
    def encode_image_to_base64(image_bytes: bytes) -> str:
        """Encode image bytes to base64 string"""
        return base64.b64encode(image_bytes).decode('utf-8')

    @staticmethod
    def resize_image(
        image_bytes: bytes,
        max_size: int = 2048
    ) -> bytes:
        """
        Resize image if larger than max_size while maintaining aspect ratio.

        Args:
            image_bytes: Original image bytes
            max_size: Maximum width or height

        Returns:
            Resized image bytes
        """
        image = Image.open(BytesIO(image_bytes))

        # Check if resize needed
        if max(image.size) <= max_size:
            return image_bytes

        # Calculate new size maintaining aspect ratio
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)

        # Resize
        resized = image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert back to bytes
        output = BytesIO()
        resized.save(output, format=image.format or 'PNG')
        return output.getvalue()

    @staticmethod
    def validate_image(image_bytes: bytes) -> bool:
        """Validate that bytes represent a valid image"""
        try:
            image = Image.open(BytesIO(image_bytes))
            image.verify()
            return True
        except Exception:
            return False

    def estimate_cost(
        self,
        num_images: int,
        tokens_per_image: int = 1000
    ) -> float:
        """
        Estimate extraction cost in USD.

        Args:
            num_images: Number of images to process
            tokens_per_image: Estimated tokens per image

        Returns:
            Estimated cost in USD
        """
        # To be overridden by specific clients
        return 0.0


class VisionModelError(Exception):
    """Base exception for vision model errors"""
    pass


class VisionModelAPIError(VisionModelError):
    """Exception for API-related errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class VisionModelRateLimitError(VisionModelError):
    """Exception for rate limit errors"""
    pass


class VisionModelTimeoutError(VisionModelError):
    """Exception for timeout errors"""
    pass
