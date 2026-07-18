"""Version 1 image annotation routes."""

import time
import json
import logging

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.image_processing import get_image_hash, extract_labels_with_cache, stream_labels_from_image, _cache_stats
from app.translation import translate_labels_with_cache, _translation_cache_stats
from app.cache import image_annotation_cache, translation_cache
from app.schema import (
    SSELabelsEventData,
    SSETranslateEventData,
    SSETranslateUpdate,
    SSEErrorEventData,
    SSECompleteEventData,
)
from app.v1 import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])

# Maximum upload size: 20 MB
MAX_UPLOAD_SIZE = 20 * 1024 * 1024


def _format_sse(event: str, data: BaseModel) -> str:
    """Format a Server-Sent Event message."""
    return f"event: {event}\ndata: {json.dumps(data.model_dump(), ensure_ascii=False)}\n\n"


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


def _validate_request(data: UploadFile, translate_language: str) -> bytes:
    """Validate upload and return binary image data."""
    # Validate upload content type
    if data.content_type and not data.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: '{data.content_type}'. Only image files are supported.",
        )

    binary_image = data.file.read()

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

    return binary_image


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

    binary_image = _validate_request(data, translate_language)

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


@router.post("/annotate/stream")
async def annotate_stream(
    data: UploadFile,
    translate: bool = False,
    translate_language: str = "english",
):
    """
    Streaming endpoint for image annotation using Server-Sent Events.

    Returns labels progressively as tiles are processed. When translation
    is enabled, original text is sent first, then translations are pushed
    as a 'translate' event after all tiles complete.

    Args:
        data: Uploaded image file
        translate: Whether to translate labels after OCR
        translate_language: Target language for translation

    Returns:
        StreamingResponse with text/event-stream content type
    """
    logger.info("Starting streaming image annotation")
    start_time = time.perf_counter()

    binary_image = _validate_request(data, translate_language)
    image_hash = get_image_hash(binary_image)
    cache_key = f"image:{image_hash}"

    # Check cache first - if cached, return immediately in a single event
    cached = image_annotation_cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit for streaming annotation (hash: {image_hash[:16]}...)")

        async def _cached_stream():
            event_data = SSELabelsEventData(tile=0, labels=cached.labels)
            yield _format_sse("labels", event_data)
            # If translation requested, translate cached labels and emit event
            if translate and cached.labels:
                from app.translation import translate_labels_with_cache
                translated = await translate_labels_with_cache(
                    cached.labels, translate_language, image_hash
                )
                updates = [
                    SSETranslateUpdate(index=i, text=l.text)
                    for i, l in enumerate(translated)
                ]
                if updates:
                    yield _format_sse("translate", SSETranslateEventData(updates=updates))
            yield _format_sse("complete", SSECompleteEventData())

        return StreamingResponse(
            _cached_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    # Build the async generator for the stream
    async def _event_stream():
        nonlocal binary_image, image_hash, cache_key
        translation_updates: list[SSETranslateUpdate] | None = [] if translate else None
        flat_labels: list = []  # Track flat index for translation updates

        async def on_tile(event_data: SSELabelsEventData):
            nonlocal flat_labels
            yield _format_sse("labels", event_data)
            if translate:
                # Track flat indices for translation
                for label in event_data.labels:
                    flat_labels.append(label)

        # We need to convert the generator-based callback to work with the stream
        # Instead, we'll use an event queue approach
        import asyncio

        event_queue: asyncio.Queue = asyncio.Queue()

        async def tile_callback(event_type: str, event_data):
            await event_queue.put((event_type, event_data))

        # Start processing in background
        process_task = asyncio.create_task(
            _process_and_stream(binary_image, tile_callback, translate, translate_language, cache_key)
        )

        # Yield events as they arrive from the queue
        labels_count = 0
        while True:
            event_type, event_data = await event_queue.get()
            if event_type == "done":
                response, translated_texts = event_data
                break
            elif event_type == "error":
                yield _format_sse("error", SSEErrorEventData(detail=str(event_data)))
                yield _format_sse("complete", SSECompleteEventData())
                return
            elif event_type == "labels":
                labels_count += len(event_data.labels)
                yield _format_sse("labels", event_data)

        # After all tiles complete, handle translation
        if translate and response and translated_texts:
            updates = []
            idx = 0
            for label in response.labels:
                if idx < len(translated_texts):
                    updates.append(SSETranslateUpdate(index=idx, text=translated_texts[idx]))
                idx += 1
            if updates:
                yield _format_sse("translate", SSETranslateEventData(updates=updates))

        # Cache the merged result for subsequent non-streaming requests
        if response:
            image_annotation_cache.set(cache_key, response)

        yield _format_sse("complete", SSECompleteEventData())

        total_duration = time.perf_counter() - start_time
        logger.info(
            f"Streaming annotation completed in {total_duration:.3f}s "
            f"with {labels_count} labels"
        )

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _process_and_stream(
    binary_image: bytes,
    tile_callback,
    translate: bool,
    translate_language: str,
    cache_key: str,
):
    """
    Process image tiles and push events to the queue.
    This runs as a background task.
    """
    import asyncio
    from app.translation import translate_labels_with_cache

    try:
        # Wrap the callback to push to the event queue
        async def on_tile_wrapper(event_data):
            await tile_callback("labels", event_data)

        image_hash = get_image_hash(binary_image)

        response = await stream_labels_from_image(binary_image, on_tile_wrapper)

        if response is None:
            await tile_callback("error", "All tiles failed to process")
            return

        translated_texts = None
        if translate and response.labels:
            translated_labels = await translate_labels_with_cache(
                response.labels, translate_language, image_hash
            )
            translated_texts = [l.text for l in translated_labels]

        await tile_callback("done", (response, translated_texts))
    except Exception as e:
        logger.error(f"Stream processing failed: {e}")
        await tile_callback("error", str(e))
