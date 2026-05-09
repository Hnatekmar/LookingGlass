import io
import hashlib
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from PIL import Image
from pydantic_ai import BinaryContent

from app.common import logger
from app.config import get_settings
from app.container import get_chat_agent
from app.schema import Label, AnnotationResponse


# Load immutable settings once for this module
settings = get_settings()

# In-memory cache for image annotations
# Structure: {cache_key: {"response": AnnotationResponse, "timestamp": float}}
_image_annotation_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl_seconds = 3600  # 1 hour default TTL
_max_cache_size = 1000  # Maximum number of cached items


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


_cache_stats = CacheStats()


def get_image_hash(binary_image: bytes) -> str:
    """Generate a SHA256 hash of the image content.
    
    Args:
        binary_image: Raw image bytes
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(binary_image).hexdigest()


def _clean_cache():
    """Remove expired entries from the cache."""
    current_time = time.time()
    expired_keys = [
        key for key, value in _image_annotation_cache.items()
        if current_time - value["timestamp"] > _cache_ttl_seconds
    ]
    for key in expired_keys:
        del _image_annotation_cache[key]
        _cache_stats.evictions += 1
    
    # Also enforce max size
    if len(_image_annotation_cache) > _max_cache_size:
        # Remove oldest entries
        sorted_keys = sorted(
            _image_annotation_cache.keys(),
            key=lambda k: _image_annotation_cache[k]["timestamp"]
        )
        keys_to_remove = sorted_keys[:len(_image_annotation_cache) - _max_cache_size]
        for key in keys_to_remove:
            del _image_annotation_cache[key]
            _cache_stats.evictions += 1


async def extract_labels_with_cache(
    binary_image: bytes,
    image_hash: str,
    cache_key: str
) -> AnnotationResponse:
    """Extract labels from image with caching support.
    
    Args:
        binary_image: Raw image bytes
        image_hash: Pre-computed image hash
        cache_key: Cache key for lookup
        
    Returns:
        AnnotationResponse with extracted labels
    """
    global _cache_stats
    
    # Clean expired entries periodically
    if len(_image_annotation_cache) % 100 == 0:
        _clean_cache()
    
    # Check cache
    if cache_key in _image_annotation_cache:
        cached = _image_annotation_cache[cache_key]
        if time.time() - cached["timestamp"] <= _cache_ttl_seconds:
            _cache_stats.hits += 1
            logger.info(f"Cache hit for image annotation (hash: {image_hash[:16]}...)")
            return cached["response"]
    
    # Cache miss - process image
    _cache_stats.misses += 1
    logger.info(f"Cache miss for image annotation (hash: {image_hash[:16]}...)")
    
    response = await _extract_labels_from_image(binary_image)
    
    # Store in cache
    _image_annotation_cache[cache_key] = {
        "response": response,
        "timestamp": time.time()
    }
    
    return response


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


async def _prepare_image_for_detection(upload_file: bytes) -> bytes:
    """Prepare image for text detection (VLM-based).

    Converts to RGB, resizes to max 1024px, and enhances contrast.
    Keeps COLOR information and improves text visibility on dark backgrounds.
    """
    from PIL import ImageEnhance
    
    image_data = io.BytesIO(upload_file)
    img = Image.open(image_data)

    # Convert to RGB if necessary (handles RGBA, grayscale, palette modes)
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

    # Resize to max 1024px while maintaining aspect ratio
    max_size = 1024
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Enhance contrast to improve text visibility, especially on dark backgrounds
    # This helps the VLM distinguish text from background more reliably
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)  # Increase contrast by 30%
    
    # Slightly enhance sharpness to make text edges clearer
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.2)  # Increase sharpness by 20%

    # Keep RGB - do NOT convert to grayscale
    # Color information helps VLM detect text regions more accurately
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=95)  # Higher quality for better detection
    return output.getvalue()




async def _extract_labels_from_image(binary_image: bytes) -> AnnotationResponse:
    """Extract text labels from an image using a labeler agent.

    Uses a vision-language model to detect text regions and extract
    their content with bounding box coordinates.
    
    NOTE: Keeps image in RGB color space for detection — color contrast
    helps the model distinguish text from background, improving recall.
    """
    logger.info("Starting label extraction from image")

    # Prepare image for detection (keep RGB for color contrast)
    scaled_image = await _prepare_image_for_detection(binary_image)

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
