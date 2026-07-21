"""Tests for the dependencies module."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_get_http_client():
    """Test that get_http_client returns an httpx client."""
    from app.dependencies import get_http_client

    settings = MagicMock()
    settings.translation_timeout = 180
    settings.glm_ocr_timeout = 60

    client = get_http_client(settings, for_translation=False)
    assert client is not None
    # Should return the same client on second call (cached)
    client2 = get_http_client(settings, for_translation=False)
    assert client is client2


def test_get_http_client_translation():
    """Test translation HTTP client uses longer timeout."""
    from app.dependencies import get_http_client

    settings = MagicMock()
    settings.translation_timeout = 300
    settings.glm_ocr_timeout = 60

    client = get_http_client(settings, for_translation=True)
    assert client is not None


def test_build_chat_agent():
    """Test that build_chat_agent returns an Agent instance."""
    from app.dependencies import build_chat_agent

    settings = MagicMock()
    settings.image_model = "test-model"
    settings.image_model_url = "http://localhost:8000/v1"
    settings.translation_model = "test-translator"
    settings.translation_model_url = "http://localhost:8001/v1"
    logger = MagicMock()

    agent = build_chat_agent(
        model="test-model",
        prompt="You are a test assistant.",
        settings_obj=settings,
        logger_obj=logger,
    )
    assert agent is not None
    assert hasattr(agent, 'run')


def test_build_chat_agent_no_url():
    """Test that missing URL raises ValueError when model doesn't match."""
    from app.dependencies import build_chat_agent

    settings = MagicMock()
    settings.image_model = "vision-model"
    settings.image_model_url = "http://vision:8000/v1"
    settings.translation_model = "trans-model"
    settings.translation_model_url = "http://trans:8001/v1"
    settings.translation_enable_thinking = False
    logger = MagicMock()

    with pytest.raises(ValueError, match="No URL configured for model"):
        build_chat_agent(
            model="unknown-model",
            prompt="test",
            settings_obj=settings,
            logger_obj=logger,
        )


@pytest.mark.asyncio
async def test_build_chat_agent_timed_run_success():
    """Test that agent.run is wrapped with timing."""
    from app.dependencies import build_chat_agent

    settings = MagicMock()
    settings.image_model = "test-model"
    settings.image_model_url = "http://localhost:8000/v1"
    settings.translation_model = "test-translator"
    settings.translation_model_url = "http://localhost:8001/v1"
    logger = MagicMock()

    agent = build_chat_agent(
        model="test-model",
        prompt="test",
        settings_obj=settings,
        logger_obj=logger,
    )

    # The original run should be wrapped
    assert hasattr(agent, 'run')


@pytest.mark.asyncio
async def test_container_get_chat_agent():
    """Test that container.get_chat_agent returns an agent."""
    from app.container import get_chat_agent

    agent = get_chat_agent(
        model="test-model",
        prompt="test",
    )
    assert agent is not None
    assert hasattr(agent, 'run')
