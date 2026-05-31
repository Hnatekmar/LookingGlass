"""
Image processing for Looking Glass.

Uses GLM-OCR for text detection with caching support.
"""

import io
import hashlib
from typing import Optional

from PIL import Image, ImageEnhance

from app.common import logger
from app.config import get_settings
from app.schema import Label, AnnotationResponse
from app.cache import image_annotation_cache, translation_cache, CacheStats
from app.glm_ocr_client import GLMOCRService


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
        for label in labels:
            label.x1 /= 999.0
            label.x2 /= 999.0
            label.y1 /= 999.0
            label.y2 /= 999.0
        
        return AnnotationResponse(labels=labels)
