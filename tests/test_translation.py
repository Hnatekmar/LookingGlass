"""Tests for the translation module."""
import pytest
from unittest.mock import patch, AsyncMock

from app.schema import Label
from app.cache import TTLCache


@pytest.mark.asyncio
async def test_translate_labels_with_cache_cache_hit():
    """Test that cached translations are returned without calling the agent."""
    from app.translation import translate_labels_with_cache, translation_cache

    labels = [Label(x1=0.0, y1=0.0, x2=0.5, y2=0.5, text="Hello")]
    image_hash = "abcdef1234567890"
    cache_key = f"translation:{image_hash}:english"

    # Pre-populate cache
    cached = [Label(x1=0.0, y1=0.0, x2=0.5, y2=0.5, text="Hola")]
    translation_cache.set(cache_key, cached)

    result = await translate_labels_with_cache(labels, "english", image_hash)
    assert result[0].text == "Hola"
    # Clean up
    translation_cache.clear()


@pytest.mark.asyncio
async def test_translate_labels_with_cache_miss():
    """Test that a cache miss triggers translation."""
    from app.translation import translate_labels_with_cache, translation_cache

    labels = [Label(x1=0.0, y1=0.0, x2=0.5, y2=0.5, text="Hello")]
    image_hash = "miss_test_hash"
    translation_cache.clear()

    # Mock the internal batch translation
    with patch("app.translation._translate_labels_batch", new_callable=AsyncMock) as mock_batch:
        mock_batch.return_value = [
            Label(x1=0.0, y1=0.0, x2=0.5, y2=0.5, text="Hola")
        ]
        result = await translate_labels_with_cache(labels, "english", image_hash)
        assert result[0].text == "Hola"
        mock_batch.assert_called_once()


@pytest.mark.asyncio
async def test_translate_text_calls_agent():
    """Test that _translate_text calls the agent and returns output."""
    from app.translation import _translate_text

    with patch("app.translation.get_chat_agent") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.run.return_value.output = "Hola"
        mock_get_agent.return_value = mock_agent

        result = await _translate_text("Hello", "english")
        assert result == "Hola"
        mock_get_agent.assert_called_once()


@pytest.mark.asyncio
async def test_translate_labels_batch_calls_agent():
    """Test batch translation calls the agent with structured output."""
    from app.translation import _translate_labels_batch

    labels = [
        Label(x1=0.0, y1=0.0, x2=0.3, y2=0.3, text="Hello"),
        Label(x1=0.5, y1=0.0, x2=0.8, y2=0.3, text="World"),
    ]

    with patch("app.translation.get_chat_agent") as mock_get_agent:
        mock_agent = AsyncMock()

        class MockTranslatedLabel:
            translated_text: str

        tl1 = MockTranslatedLabel()
        tl1.translated_text = "Hola"
        tl2 = MockTranslatedLabel()
        tl2.translated_text = "Mundo"

        mock_agent.run.return_value.output = [tl1, tl2]
        mock_get_agent.return_value = mock_agent

        result = await _translate_labels_batch(labels, "spanish")
        assert len(result) == 2
        assert result[0].text == "Hola"
        assert result[1].text == "Mundo"


@pytest.mark.asyncio
async def test_translate_labels_individual():
    """Test individual translation fallback."""
    from app.translation import _translate_labels_individual

    labels = [
        Label(x1=0.0, y1=0.0, x2=0.3, y2=0.3, text="Hello"),
    ]

    with patch("app.translation._translate_text", new_callable=AsyncMock) as mock_trans:
        mock_trans.return_value = "Bonjour"
        result = await _translate_labels_individual(labels, "french")
        assert result[0].text == "Bonjour"
        mock_trans.assert_called_once_with("Hello", "french")


def test_translation_cache_stats_accessible():
    """Test that cache stats are accessible via the cache object."""
    from app.cache import translation_cache
    stats = translation_cache.stats
    assert hasattr(stats, 'hits')
    assert hasattr(stats, 'misses')
