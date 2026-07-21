"""
Provider registry — maps provider names to ``VisionProvider`` classes.

Usage::

    from app.providers.registry import register, get_provider, list_providers

    # Providers are registered at import time by app/providers/__init__.py
    provider = get_provider(settings.ocr_provider)
    response = await provider.extract_text(image_bytes)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base import VisionProvider

_registry: dict[str, type[VisionProvider]] = {}


def register(name: str, provider_cls: type[VisionProvider]) -> None:
    """Register a provider class under *name* (e.g. ``"glm_ocr"``)."""
    _registry[name] = provider_cls


def get_provider(name: str, **kwargs: object) -> VisionProvider:
    """Return an instance of the named provider.

    Args:
        name: Provider name (must have been registered first).
        **kwargs: Extra keyword arguments forwarded to the provider constructor.

    Raises:
        KeyError: When *name* has not been registered.

    Returns:
        A fresh ``VisionProvider`` instance.
    """
    if name not in _registry:
        raise KeyError(
            f"Unknown OCR provider: {name!r}. "
            f"Available providers: {list_providers()}"
        )
    return _registry[name](**kwargs)


def list_providers() -> list[str]:
    """Return a sorted list of registered provider names."""
    return sorted(_registry)
