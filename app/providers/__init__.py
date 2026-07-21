"""
Pluggable vision/OCR provider abstraction.

Providers are registered at import time so ``get_provider()`` can resolve
them by name at runtime.
"""

from app.providers.base import VisionProvider
from app.providers.registry import register, get_provider, list_providers

# ── Register built-in providers ──────────────────────────────────────────────
# Each registration makes the provider available via ``get_provider(name)``.
from app.providers.glm_ocr_provider import GLMOCRProvider
from app.providers.gemma_provider import GemmaProvider
from app.providers.vlm_provider import VLMProvider

register("glm_ocr", GLMOCRProvider)
register("gemma", GemmaProvider)
register("vlm", VLMProvider)

__all__ = [
    "VisionProvider",
    "GLMOCRProvider",
    "GemmaProvider",
    "VLMProvider",
    "register",
    "get_provider",
    "list_providers",
]
