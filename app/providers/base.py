"""
Pluggable vision/OCR provider protocol.

All OCR / text-extraction providers must implement the ``VisionProvider``
protocol so they can be swapped transparently via the registry.
"""

from typing import Protocol

from app.schema import AnnotationResponse


class VisionProvider(Protocol):
    """Protocol for OCR / vision-model text-extraction providers.

    Every provider must expose an async ``extract_text`` method that accepts
    raw image bytes and returns an ``AnnotationResponse`` with detected text
    regions and their bounding boxes.
    """

    async def extract_text(self, image_bytes: bytes) -> AnnotationResponse:
        """Extract text labels from a raw image.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.).

        Returns:
            AnnotationResponse containing detected text labels.
        """
        ...
