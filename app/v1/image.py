"""Version 1 image annotation routes."""

import time
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.auth.access_code import AccessCodeManager
from app.auth.dependencies import require_auth
from app.container import get_access_code_manager
from app.image_processing import _extract_labels_from_image
from app.translation import _translate_labels_batch
from app.v1 import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])

# Create singleton access code manager for routes
access_code_manager_instance = get_access_code_manager()


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

    response = await _extract_labels_from_image(binary_image)

    # Step 2: Handle translation if requested
    if translate:
        translate_start = time.perf_counter()
        # Use batch translation for efficiency (single request instead of N parallel requests)
        response.labels = await _translate_labels_batch(
            response.labels, translate_language
        )
        translate_end = time.perf_counter()
        logger.info(
            f"Step 2 (batch translation) took {translate_end - translate_start:.3f}s"
        )

    total_duration = time.perf_counter() - start_time
    logger.info(f"Image annotation process completed in {total_duration:.3f}s")
    return response
