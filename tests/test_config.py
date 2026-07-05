"""Tests for the settings/config module."""

from app.config import Settings, get_settings, PROJECT_ROOT


def test_settings_defaults():
    """Test that settings are loaded and defaults are applied."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
        CANVAS_WIDTH=500,
        CANVAS_HEIGHT=500,
    )
    assert settings.image_model == "test-model"
    assert settings.translation_model == "test-translator"
    assert settings.canvas_width == 500
    assert settings.canvas_height == 500
    assert settings.default_translate_language == "english"


def test_settings_glm_ocr_defaults():
    """Test GLM-OCR default values."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.enable_glm_ocr is False
    assert settings.glm_ocr_timeout == 60
    assert settings.glm_ocr_max_tokens == 4096
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


def test_settings_redis_default():
    """Test Redis URL defaults to None."""
    settings = Settings(
        IMAGE_MODEL="test-model",
        TRANSLATION_MODEL="test-translator",
        IMAGE_MODEL_URL="http://localhost:8000/v1",
        TRANSLATION_MODEL_URL="http://localhost:8001/v1",
    )
    assert settings.redis_url is None
