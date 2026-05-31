# app/container.py
"""
Service container – builds and returns objects with explicit dependencies.

All factories pull the immutable Settings instance from ``app.config`` and the
shared logger from ``app.common``.  This centralises injection and keeps the
rest of the codebase free of hidden globals.
"""

import logging
from typing import Optional, Type

import redis.asyncio as redis

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import get_settings, Settings  # type hint for injected settings
from .common import logger
from .schema import AnnotationResponse
from .dependencies import build_chat_agent

# Module-level logger
_module_logger = logging.getLogger(__name__)


def get_chat_agent(
    model: str,
    prompt: str,
    output_type: Type = AnnotationResponse,
    settings_override: Optional[dict] = None,
):
    """Return a ready‑to‑use Agent with Settings and logger injected.

    The function fetches the singleton Settings object and forwards it, along
    with the shared ``logger``, to ``build_chat_agent`` which now expects those
    dependencies explicitly.
    """
    settings = get_settings()
    return build_chat_agent(
        model=model,
        prompt=prompt,
        output_type=output_type,
        settings_obj=settings,
        logger_obj=logger,
        settings_override=settings_override,
    )
