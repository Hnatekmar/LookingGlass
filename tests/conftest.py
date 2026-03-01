"""
Pytest configuration and fixtures.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_settings():
    """Create a mock settings object for testing."""
    mock = MagicMock()
    mock.translate_prompt_template = """
    You are a professional translator.
    Translate to {language}.
    """
    mock.translation_model = "test-model"
    mock.translation_model_samplers = None
    return mock


@pytest.fixture
def mock_chat_agent():
    """Create a mock chat agent for testing."""
    mock_agent = MagicMock()
    mock_result = MagicMock()
    mock_result.output = "Translated text"
    mock_agent.run = AsyncMock(return_value=mock_result)
    return mock_agent


@pytest.fixture
def mock_translation_response():
    """Create a mock translation response."""
    return {"translated_text": "Hello world"}


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from app.routes import app

    with (
        patch("app.translation.get_settings") as mock_get_settings,
        patch("app.translation.get_chat_agent") as mock_get_chat_agent,
    ):
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.translate_prompt_template = "Translate to {language}"
        mock_settings.translation_model = "test-model"
        mock_settings.translation_model_samplers = None

        mock_get_settings.return_value = mock_settings

        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.output = "Translated text"
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_get_chat_agent.return_value = mock_agent

        client = TestClient(app)
        yield client
