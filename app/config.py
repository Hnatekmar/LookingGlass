# app/config.py
"""
Central configuration entry point.

- Loads all settings from environment variables (via pydantic‑settings).
- Exposes a frozen, immutable Settings instance.
- Provides a `get_settings()` accessor for dependency‑injection.
"""

import os
import warnings
from pathlib import Path

from pydantic import (
    Field,
    model_validator,
)  # Import Pydantic base classes for settings management
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)  # Import BaseSettings from pydantic-settings package

# Determine the project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):  # Define Settings class inheriting from BaseSettings
    # Model names
    image_model: str = Field(
        ..., alias="IMAGE_MODEL"
    )  # Image model name from environment variable
    translation_model: str = Field(
        ..., alias="TRANSLATION_MODEL"
    )  # Translation model name from environment variable

    # Prompt template file paths
    label_prompt_path: str = Field(
        "label_detection.md", alias="LABEL_PROMPT_PATH"
    )
    translate_prompt_path: str = Field(
        "translation_single.md", alias="TRANSLATE_PROMPT_PATH"
    )
    batch_translate_prompt_path: str = Field(
        "translation_batch.md", alias="BATCH_TRANSLATE_PROMPT_PATH"
    )

    # API endpoints
    image_model_url: str = Field(
        ..., alias="IMAGE_MODEL_URL"
    )  # Image model API URL from environment variable
    translation_model_url: str = Field(
        ..., alias="TRANSLATION_MODEL_URL"
    )  # Translation model API URL from environment variable

    # Default translation language
    default_translate_language: str = Field(
        "english", alias="DEFAULT_TRANSLATE_LANGUAGE"
    )

    # ── OCR Provider Selection ────────────────────────────────────────────────
    # Which OCR / vision provider to use.  One of: "gemma", "vlm".
    ocr_provider: str = Field("gemma", alias="OCR_PROVIDER")

    # Translation model timeout (seconds) - higher for thinking mode
    translation_timeout: int = Field(600, alias="TRANSLATION_TIMEOUT")

    # ── Per-Provider Generic Configuration ────────────────────────────────────
    # Generic pattern:  OCR_PROVIDER_{NAME}_URL  /  OCR_PROVIDER_{NAME}_MODEL
    # When set these override any provider-specific fields (e.g. GEMMA_OCR_URL).
    ocr_provider_gemma_url: str | None = Field(
        None, alias="OCR_PROVIDER_GEMMA_URL"
    )
    ocr_provider_gemma_model: str | None = Field(
        None, alias="OCR_PROVIDER_GEMMA_MODEL"
    )

    # Gemma OCR Configuration (OpenAI-compatible API)
    # Backward-compatible fields used when OCR_PROVIDER_GEMMA_URL/_MODEL are unset.
    gemma_ocr_url: str = Field(
        "http://172.16.100.189:8010/v1", alias="GEMMA_OCR_URL"
    )
    gemma_ocr_model: str = Field("gemma-12b", alias="GEMMA_OCR_MODEL")
    # Gemma OCR request timeout (seconds)
    gemma_ocr_timeout: int = Field(120, alias="GEMMA_OCR_TIMEOUT")
    # Gemma OCR max tokens in response
    gemma_ocr_max_tokens: int = Field(4096, alias="GEMMA_OCR_MAX_TOKENS")

    # Application settings (centralized, replacing direct os.getenv calls)
    cors_origins: str = Field("*", alias="CORS_ORIGINS")
    api_key: str | None = Field(None, alias="API_KEY")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    port: int = Field(8000, alias="PORT")

    # Translation enable_thinking (Qwen-specific, default: disabled for speed)
    translation_enable_thinking: bool = Field(False, alias="TRANSLATION_ENABLE_THINKING")

    # ── Backward-compatible deprecated fields ─────────────────────────────────
    # These are kept as Optional so Pydantic can parse them from env vars, but
    # they are NOT used in new code.  Use ``OCR_PROVIDER`` instead.
    enable_gemma_ocr: bool | None = Field(None, alias="ENABLE_GEMMA_OCR")

    @model_validator(mode="before")
    @classmethod
    def _handle_deprecated_env_vars(cls, data: dict) -> dict:
        """Map the old ``ENABLE_GEMMA_OCR`` boolean to the new
        ``OCR_PROVIDER`` field, emitting a deprecation warning."""
        # Only apply fallback when OCR_PROVIDER is NOT explicitly set.
        explicit_provider = data.get("OCR_PROVIDER") or data.get("ocr_provider")
        if explicit_provider:
            return data

        enable_gemma = data.get("enable_gemma_ocr") or data.get("ENABLE_GEMMA_OCR")

        if enable_gemma:
            warnings.warn(
                "ENABLE_GEMMA_OCR is deprecated. Use OCR_PROVIDER=gemma instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            data["OCR_PROVIDER"] = "gemma"
            data["ocr_provider"] = "gemma"

        return data

    # Make Settings immutable – aligns with 12‑factor & code‑quality immutability
    model_config = SettingsConfigDict(
        frozen=True,
        extra="ignore",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )


# Lazy singleton: instantiated on first call to get_settings()
_settings: Settings | None = None


def get_settings() -> Settings:  # Function definition with return type hint
    """Return the shared immutable Settings instance (lazily created).

    This function is the canonical way to retrieve configuration throughout the
    codebase, enabling explicit dependency injection and easier testing.
    The Settings object is created on first access, so tests can set
    environment variables before any code calls ``get_settings()``.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
