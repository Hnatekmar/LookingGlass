"""
VLM fallback provider — uses a generic vision-language model via pydantic_ai.

This replicates the fallback path that was previously the ``else`` branch in
``image_processing._extract_labels_from_image``.
"""

import io

from PIL import Image, ImageEnhance
from pydantic_ai import BinaryContent

from app.common import logger
from app.prompts import get_prompt
from app.config import get_settings
from app.container import get_chat_agent
from app.schema import Label, AnnotationResponse


class VLMProvider:
    """Vision provider backed by a generic VLM through pydantic_ai.

    Uses the configured ``IMAGE_MODEL`` and ``IMAGE_MODEL_URL`` with the
    ``label_detection.md`` prompt to detect text regions.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def _prepare_image(self, image_bytes: bytes) -> bytes:
        """Resize and enhance contrast for VLM processing."""
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)
        return output.getvalue()

    async def extract_text(self, image_bytes: bytes) -> AnnotationResponse:
        """Run the VLM with a label-detection prompt and normalise results."""
        prepared = await self._prepare_image(image_bytes)

        labeler = get_chat_agent(
            model=self._settings.image_model,
            prompt=get_prompt(self._settings.label_prompt_path),
            output_type=list[Label],
        )

        result = await labeler.run(
            [BinaryContent(data=prepared, media_type="image/jpeg")]
        )
        labels = result.output

        # Normalise coordinates from the 0-1000 scale used in the prompt to 0-1.
        for label in labels:
            label.x1 /= 1000.0
            label.x2 /= 1000.0
            label.y1 /= 1000.0
            label.y2 /= 1000.0

        logger.info(f"VLM fallback extracted {len(labels)} text regions")
        return AnnotationResponse(labels=labels)
