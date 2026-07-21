"""Tests for the settings/config module."""

import os
import warnings
from app.config import Settings, get_settings, PROJECT_ROOT


def test_settings_defaults():
    """Test that settings are loaded and defaults are applied."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.image_model == "test-model"
    assert settings.translation_model == "test-translator"
    assert settings.default_translate_language == "english"
    assert settings.port == 8000
    assert settings.log_level == "INFO"
    assert settings.cors_origins == "*"
    assert settings.api_key is None
    assert settings.translation_enable_thinking is False


def test_settings_ocr_provider_default():
    """Test OCR_PROVIDER default value."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.ocr_provider == "glm_ocr"


def test_settings_ocr_provider_explicit():
    """Test setting OCR_PROVIDER explicitly."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
        OCR_PROVIDER="gemma",
    )
    assert settings.ocr_provider == "gemma"


def test_settings_deprecated_glm_ocr_emits_warning():
    """ENABLE_GLM_OCR emits deprecation warning and maps to OCR_PROVIDER."""
    # Unset OCR_PROVIDER so the deprecation fallback is exercised
    old_provider = os.environ.pop("OCR_PROVIDER", None)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            settings = Settings(
                IMAGE_MODEL="test-model",
                TRANSLATION_MODEL="test-translator",
                IMAGE_MODEL_URL="http://localhost:8000/v1",
                TRANSLATION_MODEL_URL="http://localhost:8001/v1",
                ENABLE_GLM_OCR=True,
            )
            assert settings.ocr_provider == "glm_ocr"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "ENABLE_GLM_OCR" in str(w[0].message)
    finally:
        if old_provider is not None:
            os.environ["OCR_PROVIDER"] = old_provider


def test_settings_deprecated_gemma_ocr_emits_warning():
    """ENABLE_GEMMA_OCR emits deprecation warning and maps to OCR_PROVIDER."""
    # Unset OCR_PROVIDER so the deprecation fallback is exercised
    old_provider = os.environ.pop("OCR_PROVIDER", None)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            settings = Settings(
                IMAGE_MODEL="test-model",
                TRANSLATION_MODEL="test-translator",
                IMAGE_MODEL_URL="http://localhost:8000/v1",
                TRANSLATION_MODEL_URL="http://localhost:8001/v1",
                ENABLE_GEMMA_OCR=True,
            )
            assert settings.ocr_provider == "gemma"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "ENABLE_GEMMA_OCR" in str(w[0].message)
    finally:
        if old_provider is not None:
            os.environ["OCR_PROVIDER"] = old_provider


def test_settings_deprecated_overridden_by_explicit():
    """Explicit OCR_PROVIDER takes precedence over deprecated booleans."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        settings = Settings(
            IMAGE_MODEL="test-model",
            TRANSLATION_MODEL="test-translator",
            IMAGE_MODEL_URL="http://localhost:8000/v1",
            TRANSLATION_MODEL_URL="http://localhost:8001/v1",
            ENABLE_GLM_OCR=True,
            OCR_PROVIDER="vlm",
        )
        # Explicit OCR_PROVIDER wins, no deprecation warning
        assert settings.ocr_provider == "vlm"
        assert len(w) == 0


def test_settings_glm_ocr_defaults():
    """Test GLM-OCR default values."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.glm_ocr_timeout == 60
    assert settings.translation_timeout == 600


def test_settings_glm_ocr_host_extraction():
    """Test host extraction from image model URL."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="https://ocr.example.com:8443/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.glm_ocr_host == "ocr.example.com"
    assert settings.glm_ocr_port == 8443


def test_settings_immutable():
    """Test that settings are frozen/immutable."""
    import pytest
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        settings.image_model = "changed"


def test_settings_project_root():
    """Test that PROJECT_ROOT points to the correct directory."""
    assert (PROJECT_ROOT / "app").is_dir()
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


def test_get_settings_returns_settings():
    """Test that get_settings() returns a Settings instance."""
    s = get_settings()
    from app.config import Settings
    assert isinstance(s, Settings)


def test_settings_new_defaults():
    """Test new config fields have correct defaults."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.port == 8000
    assert settings.log_level == "INFO"
    assert settings.cors_origins == "*"
    assert settings.api_key is None
    assert settings.translation_enable_thinking is False
    assert settings.ocr_provider == "glm_ocr"


def test_settings_gemma_defaults():
    """Test Gemma OCR default values (overridable by env vars in conftest)."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    # conftest sets GEMMA_OCR_URL / GEMMA_OCR_MODEL env vars, so the
    # values reflect those overrides.  Verify the *fields* exist.
    assert isinstance(settings.gemma_ocr_url, str)
    assert isinstance(settings.gemma_ocr_model, str)
    assert settings.gemma_ocr_timeout == 120
    assert settings.gemma_ocr_max_tokens == 4096


def test_settings_per_provider_overrides():
    """Test the generic OCR_PROVIDER_{NAME}_URL/_MODEL overrides."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
        OCR_PROVIDER_GEMMA_URL="http://override:9000/v1",
        OCR_PROVIDER_GEMMA_MODEL="override-model",
    )
    assert settings.ocr_provider_gemma_url == "http://override:9000/v1"
    assert settings.ocr_provider_gemma_model == "override-model"


def test_settings_glm_ocr_host_property():
    """Test glm_ocr_host returns correct hostname."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://api.example.com:8080/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.glm_ocr_host == "api.example.com"
    assert settings.glm_ocr_port == 8080
