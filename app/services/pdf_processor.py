"""
PDF processing service for document extraction.
Handles PDF to image conversion, preprocessing, and page management.
"""

import io
import logging
from typing import List, Tuple, Optional
from PIL import Image
import pdf2image
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF documents"""

    def __init__(
        self,
        dpi: int = 300,
        max_image_size: int = 2048,
        image_format: str = "PNG"
    ):
        """
        Initialize PDF processor.

        Args:
            dpi: DPI for PDF to image conversion (higher = better quality)
            max_image_size: Maximum width/height for output images
            image_format: Output image format (PNG, JPEG)
        """
        self.dpi = dpi
        self.max_image_size = max_image_size
        self.image_format = image_format

        logger.info(f"Initialized PDF processor: DPI={dpi}, max_size={max_image_size}, format={image_format}")

    def convert_pdf_to_images(
        self,
        pdf_bytes: bytes,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[bytes]:
        """
        Convert PDF to list of image bytes.

        Args:
            pdf_bytes: PDF file as bytes
            first_page: First page to convert (1-indexed), None for all
            last_page: Last page to convert (1-indexed), None for all

        Returns:
            List of image bytes (one per page)

        Raises:
            ValueError: If PDF is invalid or conversion fails
        """
        try:
            logger.info(f"Converting PDF to images: pages {first_page or 1} to {last_page or 'end'}")

            # Convert PDF pages to PIL Images
            images = pdf2image.convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                first_page=first_page,
                last_page=last_page,
                fmt=self.image_format.lower()
            )

            logger.info(f"Converted {len(images)} pages from PDF")

            # Convert PIL Images to bytes
            image_bytes_list = []
            for i, image in enumerate(images, start=first_page or 1):
                # Resize if needed
                if max(image.size) > self.max_image_size:
                    image = self._resize_image(image)
                    logger.debug(f"Resized page {i} to {image.size}")

                # Convert to bytes
                img_bytes = self._image_to_bytes(image)
                image_bytes_list.append(img_bytes)

            return image_bytes_list

        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            raise ValueError(f"PDF conversion failed: {str(e)}")

    def get_pdf_info(self, pdf_bytes: bytes) -> dict:
        """
        Extract metadata from PDF.

        Args:
            pdf_bytes: PDF file as bytes

        Returns:
            Dict with PDF metadata (num_pages, title, author, etc.)
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))

            metadata = {
                "num_pages": len(reader.pages),
                "title": reader.metadata.title if reader.metadata else None,
                "author": reader.metadata.author if reader.metadata else None,
                "subject": reader.metadata.subject if reader.metadata else None,
                "creator": reader.metadata.creator if reader.metadata else None,
                "producer": reader.metadata.producer if reader.metadata else None,
            }

            logger.info(f"Extracted PDF metadata: {metadata['num_pages']} pages")
            return metadata

        except Exception as e:
            logger.error(f"Failed to extract PDF info: {e}")
            raise ValueError(f"PDF info extraction failed: {str(e)}")

    def split_pdf_pages(
        self,
        pdf_bytes: bytes
    ) -> List[Tuple[int, bytes]]:
        """
        Split PDF into individual page images with page numbers.

        Args:
            pdf_bytes: PDF file as bytes

        Returns:
            List of tuples (page_number, image_bytes)
        """
        try:
            images = self.convert_pdf_to_images(pdf_bytes)
            return [(i + 1, img_bytes) for i, img_bytes in enumerate(images)]

        except Exception as e:
            logger.error(f"Failed to split PDF pages: {e}")
            raise ValueError(f"PDF splitting failed: {str(e)}")

    def preprocess_image(
        self,
        image_bytes: bytes,
        enhance_contrast: bool = True,
        remove_noise: bool = True,
        deskew: bool = False
    ) -> bytes:
        """
        Preprocess image for better OCR accuracy.

        Args:
            image_bytes: Original image bytes
            enhance_contrast: Enhance image contrast
            remove_noise: Apply noise reduction
            deskew: Correct image rotation

        Returns:
            Preprocessed image bytes
        """
        try:
            from PIL import ImageEnhance, ImageFilter

            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Enhance contrast
            if enhance_contrast:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)
                logger.debug("Enhanced image contrast")

            # Remove noise
            if remove_noise:
                image = image.filter(ImageFilter.MedianFilter(size=3))
                logger.debug("Applied noise reduction")

            # Deskew (basic rotation correction)
            if deskew:
                image = self._auto_deskew(image)
                logger.debug("Applied deskew correction")

            # Convert back to bytes
            return self._image_to_bytes(image)

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            # Return original if preprocessing fails
            return image_bytes

    def create_thumbnail(
        self,
        image_bytes: bytes,
        size: Tuple[int, int] = (200, 200)
    ) -> bytes:
        """
        Create thumbnail of image.

        Args:
            image_bytes: Original image bytes
            size: Thumbnail size (width, height)

        Returns:
            Thumbnail image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.thumbnail(size, Image.Resampling.LANCZOS)
            return self._image_to_bytes(image)

        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            raise ValueError(f"Thumbnail creation failed: {str(e)}")

    def validate_pdf(self, pdf_bytes: bytes) -> bool:
        """
        Validate that bytes represent a valid PDF.

        Args:
            pdf_bytes: PDF file bytes

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            # Check if we can read at least one page
            if len(reader.pages) > 0:
                _ = reader.pages[0]
                return True
            return False

        except Exception as e:
            logger.debug(f"PDF validation failed: {e}")
            return False

    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image maintaining aspect ratio"""
        ratio = self.max_image_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """Convert PIL Image to bytes"""
        output = io.BytesIO()
        image.save(output, format=self.image_format, quality=95)
        return output.getvalue()

    def _auto_deskew(self, image: Image.Image) -> Image.Image:
        """
        Automatically deskew (straighten) image.
        Basic implementation - for production, consider using more advanced methods.
        """
        try:
            import numpy as np
            from scipy import ndimage

            # Convert to numpy array
            img_array = np.array(image.convert('L'))

            # Find edges
            edges = np.gradient(img_array)
            edges = np.hypot(*edges)

            # Find angle
            angles = np.arange(-5, 5, 0.5)
            scores = []
            for angle in angles:
                rotated = ndimage.rotate(edges, angle, reshape=False, order=0)
                scores.append(np.sum(rotated))

            best_angle = angles[np.argmax(scores)]

            # Rotate original image
            if abs(best_angle) > 0.5:
                rotated = image.rotate(best_angle, expand=True, fillcolor='white')
                logger.debug(f"Rotated image by {best_angle} degrees")
                return rotated

            return image

        except Exception as e:
            logger.debug(f"Auto-deskew failed: {e}")
            return image

    def merge_images_to_pdf(
        self,
        image_bytes_list: List[bytes],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Merge multiple images into a single PDF.

        Args:
            image_bytes_list: List of image bytes
            output_path: Optional path to save PDF

        Returns:
            PDF file as bytes
        """
        try:
            images = [Image.open(io.BytesIO(img_bytes)) for img_bytes in image_bytes_list]

            # Convert all to RGB
            rgb_images = []
            for img in images:
                if img.mode != 'RGB':
                    rgb_images.append(img.convert('RGB'))
                else:
                    rgb_images.append(img)

            # Save as PDF
            output = io.BytesIO()
            rgb_images[0].save(
                output,
                format='PDF',
                save_all=True,
                append_images=rgb_images[1:] if len(rgb_images) > 1 else []
            )

            pdf_bytes = output.getvalue()

            # Save to file if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                logger.info(f"Saved merged PDF to {output_path}")

            return pdf_bytes

        except Exception as e:
            logger.error(f"Failed to merge images to PDF: {e}")
            raise ValueError(f"PDF merge failed: {str(e)}")
