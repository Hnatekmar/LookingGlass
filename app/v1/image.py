"""Version 1 image annotation routes."""

import time
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.auth.access_code import AccessCodeManager
from app.auth.dependencies import require_auth
from app.container import get_access_code_manager
from app.image_processing import get_image_hash, extract_labels_with_cache, _cache_stats, _clean_cache
from app.translation import translate_labels_with_cache, _translation_cache_stats, _clean_translation_cache
from app.v1 import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])

# Create singleton access code manager for routes
access_code_manager_instance = get_access_code_manager()


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring.
    
    Returns current hit/miss rates and cache size for both image annotation and translation caches.
    """
    # Import here to avoid circular imports
    from app.image_processing import _image_annotation_cache
    from app.translation import _translation_cache
    
    # Clean caches before reporting stats
    _clean_cache()
    _clean_translation_cache()
    
    return {
        "image_annotation": {
            "hits": _cache_stats.hits,
            "misses": _cache_stats.misses,
            "evictions": _cache_stats.evictions,
            "hit_rate": _cache_stats.hit_rate,
            "cache_size": len(_image_annotation_cache)
        },
        "translation": {
            "hits": _translation_cache_stats.hits,
            "misses": _translation_cache_stats.misses,
            "evictions": _translation_cache_stats.evictions,
            "hit_rate": _translation_cache_stats.hit_rate,
            "cache_size": len(_translation_cache)
        }
    }


@router.delete("/cache")
async def clear_cache():
    """Clear all cached image annotations and translations.
    
    Useful for forcing fresh processing after model updates or configuration changes.
    """
    from app.image_processing import _image_annotation_cache
    from app.translation import _translation_cache
    
    image_count = len(_image_annotation_cache)
    translation_count = len(_translation_cache)
    
    _image_annotation_cache.clear()
    _translation_cache.clear()
    
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
    user_id: str = Depends(require_auth),
    _access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
):
    """
    Post endpoint for image annotation processing.
    This endpoint accepts an image file upload and optional translation parameters
    to process and annotate the image content. The annotation process can optionally
    include language translation of any text detected in the image.
    Requires valid authentication via X-Auth-Code header.
    :param data: Uploaded image file to be annotated
    :param translate: Flag indicating whether to perform language translation on detected text
    :param translate_language: Target language for text translation, defaults to "english"
    :param user_id: Authenticated user ID (from require_auth dependency)
    :param _access_code_manager: Access code manager dependency
    :return: Processed image annotation response
    """
    logger.info(f"Starting image annotation process for user {user_id}")
    start_time = time.perf_counter()  # total processing start
    
    if translate_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: '{translate_language}'. "
                   f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES - {'none'}))}"
        )

    binary_image = await data.read()
    
    # Generate cache key for image extraction
    image_hash = get_image_hash(binary_image)
    cache_key = f"image:{image_hash}"
    
    # Try to get extracted labels from cache
    response = await extract_labels_with_cache(binary_image, image_hash, cache_key)

    # Step 2: Handle translation if requested
    if translate:
        translate_start = time.perf_counter()
        # Use batch translation for efficiency (single request instead of N parallel requests)
        response.labels = await translate_labels_with_cache(
            response.labels, translate_language, image_hash
        )
        translate_end = time.perf_counter()
        logger.info(
            f"Step 2 (batch translation) took {translate_end - translate_start:.3f}s"
        )

    total_duration = time.perf_counter() - start_time
    logger.info(f"Image annotation process completed in {total_duration:.3f}s")
    return response
