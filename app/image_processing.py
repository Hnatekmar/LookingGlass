from typing import List

from PIL import Image
from pydantic_ai import BinaryContent

from app.common import logger
from app.config import get_settings
from app.container import get_chat_agent
from app.schema import Label, AnnotationResponse


# Load immutable settings once for this module
settings = get_settings()


async def prepare_image_for_ocr(upload_file: bytes) -> bytes:
    """Prepare image for OCR processing.

    Converts to RGB, resizes to max 1024px, converts to grayscale,
    and saves as JPEG for optimal OCR performance.
    """
    image_data = io.BytesIO(upload_file)
    img = Image.open(image_data)

    if img.mode != "RGB":
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        else:
            img = img.convert("RGB")

    max_size = 1024
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    img = img.convert("L")

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=90)
    return output.getvalue()




async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    """Extract text labels from an image using a labeler agent.

    Uses a vision-language model to detect text regions and extract
    their content with bounding box coordinates.
    """
    logger.info("Starting label extraction from image")

    # Scale image for processing
    scaled_image = await prepare_image_for_ocr(binary_image)

    # Use model from settings
    labeler = get_chat_agent(
        model=settings.image_model,
        prompt=settings.label_prompt,
        output_type=list[Label],
    )

    # Extract labels
    labels = await labeler.run(
        [BinaryContent(data=scaled_image, media_type="image/jpeg")]
    )

    result: list[Label] = labels.output

    # Normalize coordinates to 0-1 range
    for e in result:
        e.x1 /= 999.0
        e.x2 /= 999.0
        e.y1 /= 999.0
        e.y2 /= 999.0

    return AnnotationResponse(labels=result)
