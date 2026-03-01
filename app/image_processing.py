import io
import json
import re
from typing import List, Tuple, Type

from PIL import Image
from pydantic_ai import BinaryContent

from app.common import logger
from app.config import get_settings
from app.container import get_chat_agent

# Load immutable settings once for this module
settings = get_settings()
from app.schema import TextBoundingBox, Label, AnnotationResponse


async def prepare_image_for_deepseek_ocr(upload_file: bytes) -> bytes:
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


def _get_image_size(image: Image.Image) -> Tuple[int, int]:
    return image.size


def parse_text_with_boxes(text: str) -> List[Label]:
    labels: List[Label] = []
    lines = text.strip().split("\n")

    for line in lines:
        pattern = r"(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)"
        matches = re.findall(pattern, line, re.DOTALL)
        try:
            _, text_content, box_str = matches[0]
        except:
            continue

        try:
            box = json.loads(box_str)
            coords = [x for x in box[0]]
            if len(coords) != 4:
                continue

            x1, y1, x2, y2 = coords
            label = Label(
                x1=x1 / 1000,
                y1=y1 / 1000,
                x2=x2 / 1000,
                y2=y2 / 1000,
                text=text_content,
            )
            labels.append(label)
        except:
            continue
    return labels


async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    logger.info("Starting label extraction from image")
    logger.info("Image opened")
    scaled_image = await prepare_image_for_deepseek_ocr(binary_image)

    labeler = get_chat_agent(
        model=settings.image_model,
        prompt=settings.label_prompt,
        output_type=list[Label],
    )

    labels_result = await labeler.run(
        [BinaryContent(data=scaled_image, media_type="image/jpeg")]
    )

    # Extract the list of Label objects from the result
    labels = labels_result.output if hasattr(labels_result, "output") else labels_result

    # Create AnnotationResponse with the labels
    result = AnnotationResponse(labels=labels)

    # Normalize coordinates to 0-1 range
    for e in result.labels:
        e.x1 /= 999.0
        e.x2 /= 999.0
        e.y1 /= 999.0
        e.y2 /= 999.0

    return result


x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3


async def _extract_labels_from_bounding_boxes(
    response_labels: List[TextBoundingBox],
) -> List[Label]:
    labels = []
    for label in response_labels:
        labels.append(
            Label(
                text=label.text,
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
    return labels


async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    logger.info("Starting label extraction from image")
    logger.info("Image opened")
    scaled_image = await prepare_image_for_deepseek_ocr(binary_image)

    labeler = get_chat_agent(
        model=settings.image_model,
        prompt=settings.label_prompt,
        output_type=list[Label],
    )

    labels = await labeler.run(
        [BinaryContent(data=scaled_image, media_type="image/jpeg")]
    )

    result = AnnotationResponse(labels=labels.output)

    for e in result.labels:
        e.x1 /= 999.0
        e.x2 /= 999.0
        e.y1 /= 999.0
        e.y2 /= 999.0

    return result


x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3


async def _extract_labels_from_bounding_boxes(
    response_labels: List[TextBoundingBox],
) -> List[Label]:
    labels = []
    for label in response_labels:
        labels.append(
            Label(
                text=label.text,
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
    return labels


async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    logger.info("Starting label extraction from image")
    logger.info("Image opened")
    scaled_image = await prepare_image_for_deepseek_ocr(binary_image)

    labeler = get_chat_agent(
        model=settings.image_model,
        prompt=settings.label_prompt,
        output_type=AnnotationResponse,
    )

    result = await labeler.run(
        [BinaryContent(data=scaled_image, media_type="image/jpeg")]
    )

    for e in result.labels:
        e.x1 /= 999.0
        e.x2 /= 999.0
        e.y1 /= 999.0
        e.y2 /= 999.0

    return result


x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3


async def _extract_labels_from_bounding_boxes(
    response_labels: List[TextBoundingBox],
) -> List[Label]:
    labels = []
    for label in response_labels:
        labels.append(
            Label(
                text=label.text,
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
    return labels


async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    logger.info("Starting label extraction from image")
    logger.info("Image opened")
    scaled_image = await prepare_image_for_deepseek_ocr(binary_image)

    labeler = get_chat_agent(
        model=settings.image_model,
        prompt=settings.label_prompt,
        output_type=list[Label],
    )

    labels = await labeler.run(
        [BinaryContent(data=scaled_image, media_type="image/jpeg")]
    )

    result: list[Label] = labels.output
    for e in result:
        e.x1 /= 999.0
        e.x2 /= 999.0
        e.y1 /= 999.0
        e.y2 /= 999.0

    return AnnotationResponse(labels=result)


x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3


async def _extract_labels_from_bounding_boxes(
    response_labels: List[TextBoundingBox],
) -> List[Label]:
    labels = []
    for label in response_labels:
        labels.append(
            Label(
                text=label.text,
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
    return labels


async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    logger.info("Starting label extraction from image")

    logger.info("Image opened")
    # Scale image for processing
    scaled_image = await prepare_image_for_deepseek_ocr(binary_image)

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


x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3


async def _extract_labels_from_bounding_boxes(
    response_labels: List[TextBoundingBox],
) -> List[Label]:
    labels = []
    for label in response_labels:
        labels.append(
            Label(
                text=label.text,
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
    return labels


async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    """Extract text labels from an image using a labeler agent."""
    logger.info("Starting label extraction from image")

    logger.info("Image opened")
    # Scale image for processing
    scaled_image = await prepare_image_for_deepseek_ocr(binary_image)

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


x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3


async def _extract_labels_from_bounding_boxes(
    response_labels: List[TextBoundingBox],
) -> List[Label]:
    """
    Extract text content from a list of labeled bounding boxes.

    This function processes a list of text bounding boxes, typically generated by an OCR system,
    and constructs a corresponding list of Label objects. Each Label encapsulates the text content
    and spatial coordinates of the original bounding box.
    """
    labels = []
    for label in response_labels:
        labels.append(
            Label(
                text=label.text,
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
    return labels
