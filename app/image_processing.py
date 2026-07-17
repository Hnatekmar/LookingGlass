"""
Image processing for Looking Glass.

Uses GLM-OCR for text detection with caching support.
Contains tile-aware functions for SSE streaming.
"""

import io
import hashlib
from typing import Callable, Coroutine, Optional

from PIL import Image, ImageEnhance

from app.common import logger
from app.config import get_settings
from app.schema import Label, AnnotationResponse, SSELabelsEventData
from app.cache import image_annotation_cache, translation_cache, CacheStats
from app.glm_ocr_client import GLMOCRService


# Default tile size and overlap for streaming
TILE_SIZE = 1024  # px
TILE_OVERLAP = 64  # px overlap to avoid cutting text regions


# Cache statistics accessor (for API endpoints)
_cache_stats = image_annotation_cache.stats


# GLM-OCR service instance (lazy-initialized)
_glm_ocr_service: Optional[GLMOCRService] = None


def _get_glm_ocr_service() -> GLMOCRService:
    """Get or create GLMOCRService singleton."""
    global _glm_ocr_service

    if _glm_ocr_service is None:
        _glm_ocr_service = GLMOCRService()

    return _glm_ocr_service


def get_image_hash(binary_image: bytes) -> str:
    """Generate a SHA256 hash of the image content."""
    return hashlib.sha256(binary_image).hexdigest()


async def prepare_image_for_glm_ocr(image_bytes: bytes) -> bytes:
    """
    Prepare image for GLM-OCR processing.

    - Resize to 1280px max (optimal for GLM-OCR)
    - Maintain RGB color
    - Apply mild sharpness enhancement
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize to GLM-OCR optimal size
    img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)

    # Mild sharpness enhancement for text edges
    img = ImageEnhance.Sharpness(img).enhance(1.15)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=95, optimize=True)

    logger.info(f"Image prepared for GLM-OCR: {img.size}")
    return output.getvalue()


def _compute_tiles(image_width: int, image_height: int) -> list[dict]:
    """
    Compute tile grid for an image.

    Returns list of tile dicts with keys: tile_index, x, y, width, height.
    Coordinates are in absolute pixels.
    """
    tiles = []
    tile_index = 0

    x = 0
    while x < image_width:
        y = 0
        while y < image_height:
            tile_w = min(TILE_SIZE, image_width - x)
            tile_h = min(TILE_SIZE, image_height - y)

            tiles.append({
                "tile_index": tile_index,
                "x": x,
                "y": y,
                "width": tile_w,
                "height": tile_h,
            })
            tile_index += 1

            y += TILE_SIZE
        x += TILE_SIZE

    return tiles


def _crop_tile(image: Image.Image, tile: dict) -> Image.Image:
    """Crop a tile region from an image, including overlap margin."""
    x = max(0, tile["x"] - TILE_OVERLAP)
    y = max(0, tile["y"] - TILE_OVERLAP)
    right = min(image.width, tile["x"] + tile["width"] + TILE_OVERLAP)
    bottom = min(image.height, tile["y"] + tile["height"] + TILE_OVERLAP)
    return image.crop((x, y, right, bottom))


def _normalize_labels(labels: list[Label], tile: dict, image_width: int, image_height: int) -> list[Label]:
    """
    Normalize tile-relative coordinates to image-relative (0-1 range).
    """
    normalized = []
    for label in labels:
        # Tile-relative -> image-relative
        abs_x1 = tile["x"] + label.x1 * tile["width"]
        abs_y1 = tile["y"] + label.y1 * tile["height"]
        abs_x2 = tile["x"] + label.x2 * tile["width"]
        abs_y2 = tile["y"] + label.y2 * tile["height"]

        normalized.append(Label(
            x1=abs_x1 / image_width,
            y1=abs_y1 / image_height,
            x2=abs_x2 / image_width,
            y2=abs_y2 / image_height,
            text=label.text,
        ))

    return normalized


def _deduplicate_labels(labels: list[Label], iou_threshold: float = 0.5) -> list[Label]:
    """
    Deduplicate labels by removing overlapping boxes (IOU > threshold).
    Keeps the label with the longer text.
    """
    if len(labels) <= 1:
        return labels

    def iou(a: Label, b: Label) -> float:
        x1 = max(a.x1, b.x1)
        y1 = max(a.y1, b.y1)
        x2 = min(a.x2, b.x2)
        y2 = min(a.y2, b.y2)
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area_a = (a.x2 - a.x1) * (a.y2 - a.y1)
        area_b = (b.x2 - b.x1) * (b.y2 - b.y1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    kept = []
    for label in labels:
        duplicate = False
        for i, existing in enumerate(kept):
            if iou(label, existing) > iou_threshold:
                # Keep the one with longer text
                if len(label.text) > len(existing.text):
                    kept[i] = label
                duplicate = True
                break
        if not duplicate:
            kept.append(label)

    return kept


async def stream_labels_from_image(
    binary_image: bytes,
    on_tile: Callable[[SSELabelsEventData], Coroutine],
) -> Optional[AnnotationResponse]:
    """
    Extract labels with per-tile streaming via callback.

    Splits the image into tiles, processes each tile via the OCR engine,
    and invokes `on_tile(data)` for each completed tile.

    Returns the merged AnnotationResponse (all tiles combined, deduplicated),
    or None if processing failed entirely.
    """
    img = Image.open(io.BytesIO(binary_image))
    if img.mode != "RGB":
        img = img.convert("RGB")

    image_width, image_height = img.size
    tiles = _compute_tiles(image_width, image_height)

    all_labels: list[Label] = []
    failed_tiles = 0

    for tile in tiles:
        try:
            tile_img = _crop_tile(img, tile)
            tile_bytes = io.BytesIO()
            tile_img.save(tile_bytes, format="JPEG", quality=95)
            tile_bytes = tile_bytes.getvalue()

            tile_response = await _extract_labels_from_image(tile_bytes)
            tile_labels = _normalize_labels(
                tile_response.labels, tile, image_width, image_height
            )

            event_data = SSELabelsEventData(tile=tile["tile_index"], labels=tile_labels)
            await on_tile(event_data)

            all_labels.extend(tile_labels)
        except Exception as e:
            logger.error(f"Tile {tile['tile_index']} processing failed: {e}")
            failed_tiles += 1
            # Yield empty event for failed tile so client knows
            event_data = SSELabelsEventData(tile=tile["tile_index"], labels=[])
            await on_tile(event_data)

    if not all_labels and failed_tiles == len(tiles):
        logger.error("All tiles failed to process")
        return None

    # Merge and deduplicate all labels
    merged_labels = _deduplicate_labels(all_labels)

    logger.info(
        f"Streaming complete: {len(tiles)} tiles, "
        f"{len(all_labels)} raw labels, {len(merged_labels)} after dedup, "
        f"{failed_tiles} failed tiles"
    )
    return AnnotationResponse(labels=merged_labels)


async def extract_labels_with_cache(
    binary_image: bytes,
    image_hash: str,
    cache_key: str,
    **kwargs,  # Ignored - kept for backward compatibility
) -> AnnotationResponse:
    """
    Extract labels from image with caching support.

    Args:
        binary_image: Raw image bytes
        image_hash: Pre-computed image hash
        cache_key: Cache key for lookup
        kwargs: Ignored (kept for backward compatibility with tiling params)

    Returns:
        AnnotationResponse with extracted labels
    """
    # Check cache
    cached = image_annotation_cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit for image annotation (hash: {image_hash[:16]}...)")
        return cached

    # Cache miss - process image
    logger.info(f"Cache miss for image annotation (hash: {image_hash[:16]}...)")

    response = await _extract_labels_from_image(binary_image)

    # Store in cache
    image_annotation_cache.set(cache_key, response)

    return response


async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    """
    Extract text labels from an image using GLM-OCR.
    """
    settings = get_settings()

    if settings.enable_glm_ocr:
        logger.info("Using GLM-OCR for text detection")
        glm_ocr_service = _get_glm_ocr_service()
        return await glm_ocr_service.extract_text_with_bboxes(binary_image)
    else:
        # Fallback to VLM-based detection (simplified, no tiling)
        logger.info("Using VLM fallback for text detection")
        from app.container import get_chat_agent
        from pydantic_ai import BinaryContent

        # Prepare image for VLM
        img = Image.open(io.BytesIO(binary_image))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.3)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)

        labeler = get_chat_agent(
            model=settings.image_model,
            prompt=settings.label_prompt,
            output_type=list[Label],
        )

        result = await labeler.run([BinaryContent(data=output.getvalue(), media_type="image/jpeg")])
        labels = result.output

        # Normalize coordinates to 0-1 range
        # Label prompt specifies 0-1000 coordinate scale, so divide by 1000.0
        for label in labels:
            label.x1 /= 1000.0
            label.x2 /= 1000.0
            label.y1 /= 1000.0
            label.y2 /= 1000.0

        return AnnotationResponse(labels=labels)
