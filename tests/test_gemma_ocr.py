"""Tests for the Gemma OCR client module."""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.schema import AnnotationResponse, Label


@pytest.mark.asyncio
async def test_gemma_ocr_service_initialization():
    """Test that GemmaOCRService initializes with config values."""
    from app.gemma_ocr_client import GemmaOCRService
    from app.config import get_settings

    settings = get_settings()

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client:
        service = GemmaOCRService()
        assert service.api_url == settings.gemma_ocr_url.rstrip("/") + "/chat/completions"
        assert service.model == settings.gemma_ocr_model
        assert service.timeout == settings.gemma_ocr_timeout
        mock_client.assert_called_once()


@pytest.mark.asyncio
async def test_gemma_ocr_extract_text_valid_response():
    """Test parsing a valid API response."""
    from app.gemma_ocr_client import GemmaOCRService

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "labels": [
                            {"x1": 100, "y1": 200, "x2": 500, "y2": 400, "text": "Hello World"},
                            {"x1": 50, "y1": 50, "x2": 200, "y2": 150, "text": "Sample Text"},
                        ]
                    })
                }
            }
        ]
    }

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_client.post = AsyncMock(return_value=mock_response)

        service = GemmaOCRService()
        result = await service.extract_text_with_bboxes(b"fake-image-bytes")

        assert isinstance(result, AnnotationResponse)
        assert len(result.labels) == 2
        assert result.labels[0].text == "Hello World"
        assert result.labels[0].x1 == 100 / 1000.0
        assert result.labels[0].y1 == 200 / 1000.0
        assert result.labels[0].x2 == 500 / 1000.0
        assert result.labels[0].y2 == 400 / 1000.0
        assert result.labels[1].text == "Sample Text"


@pytest.mark.asyncio
async def test_gemma_ocr_extract_text_empty_response():
    """Test handling of empty response."""
    from app.gemma_ocr_client import GemmaOCRService

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"labels": []})
                }
            }
        ]
    }

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_client.post = AsyncMock(return_value=mock_response)

        service = GemmaOCRService()
        result = await service.extract_text_with_bboxes(b"fake-image-bytes")

        assert isinstance(result, AnnotationResponse)
        assert len(result.labels) == 0


@pytest.mark.asyncio
async def test_gemma_ocr_extract_text_invalid_json_in_response():
    """Test handling of invalid JSON in model response."""
    from app.gemma_ocr_client import GemmaOCRService

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "This is not valid JSON"
                }
            }
        ]
    }

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_client.post = AsyncMock(return_value=mock_response)

        service = GemmaOCRService()
        result = await service.extract_text_with_bboxes(b"fake-image-bytes")

        assert isinstance(result, AnnotationResponse)
        assert len(result.labels) == 0  # Should gracefully return empty


@pytest.mark.asyncio
async def test_gemma_ocr_http_error():
    """Test that HTTP errors are propagated."""
    from app.gemma_ocr_client import GemmaOCRService
    import httpx

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=MagicMock(status_code=400, text="Bad request"),
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        service = GemmaOCRService()
        with pytest.raises(httpx.HTTPStatusError):
            await service.extract_text_with_bboxes(b"fake-image-bytes")


@pytest.mark.asyncio
async def test_gemma_ocr_request_error():
    """Test that connection errors are propagated."""
    from app.gemma_ocr_client import GemmaOCRService
    import httpx

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection refused", request=MagicMock()))

        service = GemmaOCRService()
        with pytest.raises(httpx.RequestError):
            await service.extract_text_with_bboxes(b"fake-image-bytes")


def test_safe_float():
    """Test the safe_float utility."""
    from app.gemma_ocr_client import GemmaOCRService

    assert GemmaOCRService._safe_float(42) == 42.0
    assert GemmaOCRService._safe_float("3.14") == 3.14
    assert GemmaOCRService._safe_float(None) == 0.0
    assert GemmaOCRService._safe_float("invalid") == 0.0
    assert GemmaOCRService._safe_float("", default=1.0) == 1.0


def test_gemma_ocr_system_prompt_exists():
    """Test that the module-level system prompt is defined."""
    from app.gemma_ocr_client import GEMMA_OCR_SYSTEM_PROMPT
    assert GEMMA_OCR_SYSTEM_PROMPT is not None
    assert len(GEMMA_OCR_SYSTEM_PROMPT) > 100
    assert "labels" in GEMMA_OCR_SYSTEM_PROMPT
    assert "OCR" in GEMMA_OCR_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_gemma_ocr_parse_alternative_field_names():
    """Test parsing of alternative field names (left/top/right/bottom, content)."""
    from app.gemma_ocr_client import GemmaOCRService

    # Test with alternative field names
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "regions": [
                            {"left": 100, "top": 200, "right": 500, "bottom": 400, "content": "Alt Fields"}
                        ]
                    })
                }
            }
        ]
    }

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_client.post = AsyncMock(return_value=mock_response)

        service = GemmaOCRService()
        result = await service.extract_text_with_bboxes(b"fake-image-bytes")

        assert len(result.labels) == 1
        assert result.labels[0].text == "Alt Fields"
        assert result.labels[0].x1 == 100 / 1000.0
        assert result.labels[0].y1 == 200 / 1000.0
        assert result.labels[0].x2 == 500 / 1000.0
        assert result.labels[0].y2 == 400 / 1000.0


@pytest.mark.asyncio
async def test_gemma_ocr_parse_direct_array():
    """Test parsing when model returns a direct array instead of named dict."""
    from app.gemma_ocr_client import GemmaOCRService

    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps([
                        {"x1": 0, "y1": 0, "x2": 1000, "y2": 1000, "text": "Direct Array"}
                    ])
                }
            }
        ]
    }

    with patch("app.gemma_ocr_client.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_client.post = AsyncMock(return_value=mock_response)

        service = GemmaOCRService()
        result = await service.extract_text_with_bboxes(b"fake-image-bytes")

        assert len(result.labels) == 1
        assert result.labels[0].text == "Direct Array"


@pytest.mark.asyncio
async def test_gemma_ocr_image_processing_integration():
    """Test the integration point in image_processing module.

    Verifies that _extract_labels_from_image routes to Gemma OCR when
    enable_gemma_ocr is True.
    """
    from app.image_processing import _extract_labels_from_image
    from app.schema import AnnotationResponse, Label

    with patch("app.image_processing.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.enable_gemma_ocr = True
        mock_settings.enable_glm_ocr = False
        mock_get_settings.return_value = mock_settings

        with patch("app.image_processing._get_gemma_ocr_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.extract_text_with_bboxes.return_value = AnnotationResponse(
                labels=[Label(x1=0.1, y1=0.2, x2=0.5, y2=0.6, text="Gemma OCR")]
            )
            mock_get_service.return_value = mock_service

            with patch("app.image_processing.prepare_image_for_glm_ocr", new_callable=AsyncMock) as mock_prep:
                mock_prep.return_value = b"prepared-image"

                result = await _extract_labels_from_image(b"raw-image")

                assert len(result.labels) == 1
                assert result.labels[0].text == "Gemma OCR"
                mock_prep.assert_called_once_with(b"raw-image")
                mock_service.extract_text_with_bboxes.assert_called_once_with(b"prepared-image")
