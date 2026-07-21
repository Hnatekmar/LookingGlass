"""
Gemma OCR provider — wraps ``GemmaOCRService`` via an OpenAI-compatible API.

Image pre-processing (resize, sharpness enhancement) is handled inside this
provider so the underlying service stays simple.
"""

import io

from PIL import Image, ImageEnhance

from app.common import logger
from app.gemma_ocr_client import GemmaOCRService
from app.schema import AnnotationResponse


class GemmaProvider:
    """Vision provider backed by Gemma 12B (or any OpenAI-compatible VLM)."""

    def __init__(self) -> None:
        self._service = GemmaOCRService()

    async def _prepare_image(self, image_bytes: bytes) -> bytes:
        """Resize and sharpen the image for optimal VLM OCR throughput."""
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
        img = ImageEnhance.Sharpness(img).enhance(1.15)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95, optimize=True)
        logger.info(f"Image prepared for Gemma OCR: {img.size}")
        return output.getvalue()

    async def extract_text(self, image_bytes: bytes) -> AnnotationResponse:
        """Prepare the image then delegate to ``GemmaOCRService``."""
        prepared = await self._prepare_image(image_bytes)
        return await self._service.extract_text_with_bboxes(prepared)
