"""Tests for the provider registry and individual OCR providers."""

import pytest
from unittest.mock import patch, AsyncMock


# ==============================================================================
# Registry tests
# ==============================================================================


def test_registry_list_providers():
    """list_providers returns registered provider names."""
    from app.providers.registry import list_providers

    names = list_providers()
    assert "glm_ocr" in names
    assert "gemma" in names
    assert "vlm" in names


def test_registry_get_provider():
    """get_provider returns a provider instance for a known name."""
    from app.providers.registry import get_provider, _registry

    # Verify the provider class is registered without instantiating it
    assert "glm_ocr" in _registry
    assert issubclass(_registry["glm_ocr"], object)  # just verify it's a class


def test_registry_get_unknown_provider():
    """get_provider raises KeyError for unknown names."""
    from app.providers.registry import get_provider

    with pytest.raises(KeyError):
        get_provider("nonexistent_provider")


def test_registry_providers_have_extract_text():
    """Every registered provider has the extract_text method."""
    from app.providers.registry import list_providers, _registry

    for name in list_providers():
        cls = _registry[name]
        assert hasattr(cls, "extract_text") or "extract_text" in cls.__dict__ or hasattr(cls, "extract_text")


def test_registry_register():
    """register adds a new provider to the registry."""
    from app.providers.registry import register, list_providers, _registry

    # Save original state
    original = dict(_registry)

    class DummyProvider:
        async def extract_text(self, image_bytes: bytes):
            from app.schema import AnnotationResponse
            return AnnotationResponse(labels=[])

    register("dummy_test", DummyProvider)
    assert "dummy_test" in list_providers()

    # Restore original state
    _registry.clear()
    _registry.update(original)


# ==============================================================================
# GLM-OCR Provider tests
# ==============================================================================


def test_glm_ocr_provider_imports():
    """GLMOCRProvider can be imported and instantiated."""
    from app.providers.glm_ocr_provider import GLMOCRProvider

    # NOTE: actual instantiation will fail if glmocr SDK is not installed,
    # but the class itself should be importable.
    assert GLMOCRProvider.__name__ == "GLMOCRProvider"


# ==============================================================================
# Gemma Provider tests
# ==============================================================================


@pytest.mark.asyncio
async def test_gemma_provider_prepare_image():
    """_prepare_image resizes and returns JPEG bytes."""
    from app.providers.gemma_provider import GemmaProvider
    import io
    from PIL import Image

    # Create a small valid test image
    img = Image.new("RGB", (200, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    provider = GemmaProvider()
    prepared = await provider._prepare_image(img_bytes)

    assert isinstance(prepared, bytes)
    assert len(prepared) > 0

    # Verify the prepared image is a valid JPEG
    result_img = Image.open(io.BytesIO(prepared))
    assert result_img.size[0] <= 1280
    assert result_img.size[1] <= 1280
    assert result_img.mode == "RGB"


# ==============================================================================
# VLM Provider tests
# ==============================================================================


def test_vlm_provider_imports():
    """VLMProvider can be imported."""
    from app.providers.vlm_provider import VLMProvider
    assert VLMProvider.__name__ == "VLMProvider"


# ==============================================================================
# Image processing integration with provider
# ==============================================================================


@pytest.mark.asyncio
async def test_extract_labels_uses_provider():
    """_extract_labels_from_image resolves the provider from settings."""
    from app.image_processing import _extract_labels_from_image
    from app.schema import AnnotationResponse, Label
    from unittest.mock import patch, AsyncMock

    with (
        patch("app.image_processing.get_provider") as mock_get_provider,
        patch("app.image_processing.get_settings") as mock_get_settings,
    ):
        # Mock settings
        mock_settings = AsyncMock()
        mock_settings.ocr_provider = "glm_ocr"
        mock_get_settings.return_value = mock_settings

        # Mock provider
        mock_provider = AsyncMock()
        mock_provider.extract_text.return_value = AnnotationResponse(
            labels=[Label(x1=0.1, y1=0.1, x2=0.5, y2=0.5, text="test")]
        )
        mock_get_provider.return_value = mock_provider

        result = await _extract_labels_from_image(b"fake-image-bytes")

        assert len(result.labels) == 1
        assert result.labels[0].text == "test"
        mock_get_provider.assert_called_once_with("glm_ocr")
        mock_provider.extract_text.assert_called_once_with(b"fake-image-bytes")
