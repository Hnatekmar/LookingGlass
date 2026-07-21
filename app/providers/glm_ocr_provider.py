"""
GLM-OCR provider — wraps the official ``GLMOCRService``.

Configuration is managed via ``Settings`` (``IMAGE_MODEL_URL`` and
``IMAGE_MODEL`` are used to initialise the GLM-OCR SDK client).
"""

from app.schema import AnnotationResponse
from app.glm_ocr_client import GLMOCRService


class GLMOCRProvider:
    """Vision provider backed by the official GLM-OCR SDK."""

    def __init__(self) -> None:
        self._service = GLMOCRService()

    async def extract_text(self, image_bytes: bytes) -> AnnotationResponse:
        """Delegate to ``GLMOCRService.extract_text_with_bboxes``."""
        return await self._service.extract_text_with_bboxes(image_bytes)
