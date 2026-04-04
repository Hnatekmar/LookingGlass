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

from pydantic_ai import ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import get_settings, Settings  # type hint for injected settings
from .schema import AnnotationResponse
from .auth.store import AccessCodeStore, InMemoryAccessCodeStore
from .auth.store_redis import RedisAccessCodeStore
from .auth.oauth2 import OAuth2Client
from .auth.access_code import AccessCodeManager

from .dependencies import build_chat_agent

# Module-level logger
_module_logger = logging.getLogger(__name__)

# Auth dependencies - singletons
_access_code_store: AccessCodeStore | None = None
_access_code_manager: AccessCodeManager | None = None
_redis_client: redis.Redis | None = None


def _get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton.

    Returns:
        Async Redis client instance.

    Raises:
        RuntimeError: If Redis connection fails.
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    redis_url = settings.redis_url

    if not redis_url:
        raise RuntimeError("Redis URL not configured")

    try:
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False,  # We handle bytes for user_id
            max_connections=20,
        )
        # Test connection
        import asyncio

        asyncio.get_event_loop().run_until_complete(_redis_client.ping())
        _module_logger.info("Redis connection established")
        return _redis_client
    except Exception as e:
        _module_logger.error(f"Failed to connect to Redis: {e}")
        raise RuntimeError(f"Redis connection failed: {e}") from e


def get_access_code_store() -> AccessCodeStore:
    """Get the access code store (singleton).

    Returns Redis-backed store if REDIS_URL is configured,
    otherwise falls back to in-memory store (with warning).

    Returns:
        AccessCodeStore instance (Redis or in-memory).
    """
    global _access_code_store

    if _access_code_store is not None:
        return _access_code_store

    settings = get_settings()

    # Use Redis if configured
    if settings.redis_url:
        try:
            redis_client = _get_redis_client()
            _access_code_store = RedisAccessCodeStore(
                redis_client=redis_client,
                ttl=settings.access_code_ttl,
            )
            _module_logger.info("Using RedisAccessCodeStore")
        except RuntimeError as e:
            # Redis unavailable, fall back to in-memory with warning
            _module_logger.warning(
                f"Redis unavailable, falling back to InMemoryAccessCodeStore: {e}. "
                "WARNING: Codes will be lost on restart and not shared across replicas."
            )
            _access_code_store = InMemoryAccessCodeStore()
    else:
        # No Redis configured, use in-memory with warning in production
        _module_logger.warning(
            "No Redis configured, using InMemoryAccessCodeStore. "
            "WARNING: Codes will be lost on restart and not shared across replicas. "
            "Set REDIS_URL for production deployments."
        )
        _access_code_store = InMemoryAccessCodeStore()

    return _access_code_store


def get_oauth2_client() -> OAuth2Client:
    """Get the OAuth2 client."""
    settings = get_settings()
    return OAuth2Client(settings)


def get_access_code_manager() -> AccessCodeManager:
    """Get the access code manager (singleton).

    Returns:
        AccessCodeManager instance with injected store and OAuth2 client.
    """
    global _access_code_manager

    if _access_code_manager is not None:
        return _access_code_manager

    store = get_access_code_store()
    oauth2_client = get_oauth2_client()
    _access_code_manager = AccessCodeManager(store, oauth2_client)

    return _access_code_manager



def get_chat_agent(
    model: str,
    prompt: str,
    output_type: Type = AnnotationResponse,
    settings_override: Optional[ModelSettings] = None,
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
