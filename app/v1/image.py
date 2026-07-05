"""Version 1 image annotation routes."""

import time
import logging

from fastapi import APIRouter, HTTPException, UploadFile

from app.image_processing import get_image_hash, extract_labels_with_cache, _cache_stats
from app.translation import translate_labels_with_cache, _translation_cache_stats
from app.cache import image_annotation_cache, translation_cache
from app.v1 import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])

# Maximum upload size: 20 MB
MAX_UPLOAD_SIZE = 20 * 1024 * 1024


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring."""
    return {
        "image_annotation": {
            "hits": _cache_stats.hits,
            "misses": _cache_stats.misses,
            "evictions": _cache_stats.evictions,
            "hit_rate": _cache_stats.hit_rate,
            "cache_size": len(image_annotation_cache)
        },
        "translation": {
            "hits": _translation_cache_stats.hits,
            "misses": _translation_cache_stats.misses,
            "evictions": _translation_cache_stats.evictions,
            "hit_rate": _translation_cache_stats.hit_rate,
            "cache_size": len(translation_cache)
        }
    }


@router.delete("/cache")
async def clear_cache():
    """Clear all cached image annotations and translations."""
    image_count = len(image_annotation_cache)
    translation_count = len(translation_cache)
    
    image_annotation_cache.clear()
    translation_cache.clear()
    
    logger.info(f"Cache cleared: {image_count} image annotations, {translation_count} translations")
    
    return {
        "cleared": {
            "image_annotations": image_count,
            "translations": translation_count
        }
    }


@router.post("/annotate/")
@router.post("/annotate")
async def annotate(
    data: UploadFile,
    translate: bool = False,
    translate_language: str = "english",
):
    """
    Post endpoint for image annotation processing.
    
    Args:
        data: Uploaded image file to be annotated
        translate: Flag indicating whether to perform language translation
        translate_language: Target language for translation, defaults to "english"
    
    Returns:
        Processed image annotation response
    """
    logger.info("Starting image annotation")
    start_time = time.perf_counter()
    
    # Validate upload content type
    if data.content_type and not data.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: '{data.content_type}'. Only image files are supported.",
        )

    binary_image = await data.read()

    # Validate upload size
    if len(binary_image) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(binary_image)} bytes. Maximum allowed size is {MAX_UPLOAD_SIZE} bytes.",
        )

    if translate_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: '{translate_language}'. "
                   f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES - {'none'}))}"
        )

    # Generate cache key
    image_hash = get_image_hash(binary_image)
    cache_key = f"image:{image_hash}"
    
    # Extract labels from image
    response = await extract_labels_with_cache(
        binary_image,
        image_hash,
        cache_key,
    )

    # Handle translation if requested
    if translate:
        translate_start = time.perf_counter()
        response.labels = await translate_labels_with_cache(
            response.labels, translate_language, image_hash
        )
        translate_end = time.perf_counter()
        logger.info(f"Translation completed in {translate_end - translate_start:.3f}s")

    total_duration = time.perf_counter() - start_time
    logger.info(f"Image annotation completed in {total_duration:.3f}s")
    return response
