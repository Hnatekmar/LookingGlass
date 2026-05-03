"""Version 1 translation routes."""

import time
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.access_code import AccessCodeManager
from app.auth.dependencies import require_auth
from app.container import get_access_code_manager
from app.translation import _translate_text
from app.v1 import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translate", tags=["translate"])

# Create singleton access code manager for routes
access_code_manager_instance = get_access_code_manager()


class TranslateRequest(BaseModel):
    text: str


@router.post("/")
@router.post("")
async def translate(
    request: TranslateRequest,
    target_language: str = "english",
    user_id: str = Depends(require_auth),
    _access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
):
    """
    Post endpoint for text translation.
    This endpoint accepts a text string and translates it to the specified language.
    Requires valid authentication via X-Auth-Code header.
    :param request: Request body containing the text to translate
    :param target_language: Target language for translation, defaults to 'english'
    :param user_id: Authenticated user ID (from require_auth dependency)
    :param _access_code_manager: Access code manager dependency
    :return: Translated text response
    """
    # Reject unknown language names to prevent prompt injection
    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: '{target_language}'. "
                   f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES - {'none'}))}"
        )

    logger.info(f"Starting translation to {target_language} for user {user_id}")
    start_time = time.perf_counter()

    translated_text = await _translate_text(request.text, target_language)

    total_duration = time.perf_counter() - start_time
    logger.info(f"Translation completed in {total_duration:.3f}s")
    return {"translated_text": translated_text}
