"""
Tests for the translation endpoint.

This test suite covers:
- Happy path scenarios
- Edge cases (empty text, special characters, Unicode)
- Error handling
- Concurrent requests
- Parameter validation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# Test data constants
TEST_TEXTS = {
    "simple": "Hello world",
    "empty": "",
    "whitespace": "   ",
    "unicode": "Héllo wörld 你好 🌍",
    "long": "A" * 1000,
    "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
    "mixed": "Hello 世界 مرحبا 🌟",
    "already_english": "This is already in English",
}


class TestTranslationEndpoint:
    """Test suite for the /translate/ endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        with (
            patch("app.translation.get_settings") as mock_get_settings,
            patch("app.translation.get_chat_agent") as mock_get_chat_agent,
        ):
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

            from app.routes import app

            client = TestClient(app, raise_server_exceptions=False)
            yield client

    # ==================== Happy Path Tests ====================

    def test_translate_simple_text(self, client):
        """Test basic translation with simple text."""
        response = client.post("/translate/", json={"text": "Hello world"})

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data
        assert data["translated_text"] is not None

    def test_translate_with_explicit_language(self, client):
        """Test translation with explicit target language."""
        response = client.post(
            "/translate/?target_language=french", json={"text": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data

    def test_translate_with_query_params(self, client):
        """Test translation using query parameters."""
        response = client.post(
            "/translate/?target_language=spanish", json={"text": "Good morning"}
        )

        assert response.status_code == 200
        assert response.json()["translated_text"] is not None

    def test_translate_default_language(self, client):
        """Test that default language is English when not specified."""
        response = client.post("/translate/", json={"text": "Bonjour"})

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data

    # ==================== Edge Case Tests ====================

    def test_translate_empty_text(self, client):
        """Test translation of empty string."""
        response = client.post("/translate/", json={"text": ""})

        # Should handle gracefully - either return empty or error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "translated_text" in data

    def test_translate_whitespace_only(self, client):
        """Test translation of whitespace-only text."""
        response = client.post("/translate/", json={"text": "   "})

        assert response.status_code in [200, 400]

    def test_translate_unicode_characters(self, client):
        """Test translation with Unicode characters."""
        unicode_text = "Héllo wörld 你好 🌍"
        response = client.post("/translate/", json={"text": unicode_text})

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data

    def test_translate_special_characters(self, client):
        """Test translation with special characters."""
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        response = client.post("/translate/", json={"text": special_text})

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data

    def test_translate_mixed_languages(self, client):
        """Test translation with mixed language text."""
        mixed_text = "Hello 世界 مرحبا 🌟"
        response = client.post("/translate/", json={"text": mixed_text})

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data

    def test_translate_long_text(self, client):
        """Test translation of long text (1000 chars)."""
        long_text = "A" * 1000
        response = client.post("/translate/", json={"text": long_text})

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data
        assert len(data["translated_text"]) > 0

    def test_translate_newlines_and_tabs(self, client):
        """Test translation with newlines and tabs."""
        formatted_text = "Line 1\nLine 2\tTabbed"
        response = client.post("/translate/", json={"text": formatted_text})

        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data

    # ==================== Error Handling Tests ====================

    def test_translate_missing_text_field(self, client):
        """Test request without text field."""
        response = client.post("/translate/", json={})

        assert response.status_code == 422  # Validation error

    def test_translate_null_text(self, client):
        """Test request with null text."""
        response = client.post("/translate/", json={"text": None})

        assert response.status_code == 422  # Validation error

    def test_translate_invalid_json(self, client):
        """Test request with invalid JSON."""
        response = client.post(
            "/translate/",
            content="invalid json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 422

    def test_translate_wrong_method(self, client):
        """Test using wrong HTTP method."""
        response = client.get("/translate/")

        assert response.status_code == 405  # Method not allowed

    def test_translate_nonexistent_endpoint(self, client):
        """Test accessing nonexistent endpoint."""
        response = client.post("/translate")  # Missing trailing slash

        # Should redirect or return 404 or 422
        assert response.status_code in [307, 404, 422]

    # ==================== Integration Tests ====================

    def test_translate_with_various_languages(self, client):
        """Test translation with different target languages."""
        with patch("app.translation._translate_text") as mock_translate_text:
            mock_translate_text.return_value = "Result"

            languages = ["french", "german", "spanish", "japanese", "chinese"]

            for lang in languages:
                response = client.post(
                    f"/translate/?target_language={lang}", json={"text": "Test"}
                )
                assert response.status_code == 200

    # ==================== Concurrent Request Tests ====================

    def test_concurrent_translations(self, client):
        """Test multiple concurrent translation requests."""

        async def make_request(text):
            response = client.post("/translate/", json={"text": text})
            return response.status_code

        async def run_concurrent_tests():
            # Make 5 concurrent requests
            tasks = [make_request(f"Request {i}") for i in range(5)]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(run_concurrent_tests())

        # All requests should succeed
        assert all(status == 200 for status in results)

    # ==================== Response Validation Tests ====================

    def test_response_format(self, client):
        """Test that response has correct format."""
        response = client.post("/translate/", json={"text": "Test"})

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert isinstance(data, dict)
        assert "translated_text" in data
        assert isinstance(data["translated_text"], str)

    def test_response_not_empty(self, client):
        """Test that response is not empty."""
        response = client.post("/translate/", json={"text": "Test"})

        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] != ""

    def test_response_encoding(self, client):
        """Test that response handles UTF-8 encoding correctly."""
        unicode_text = "Hello 你好 مرحبا שלום"
        response = client.post("/translate/", json={"text": unicode_text})

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    # ==================== Performance Tests ====================

    def test_translation_timing(self, client):
        """Test that translation completes in reasonable time."""
        import time

        start = time.time()
        response = client.post("/translate/", json={"text": "Test"})
        duration = time.time() - start

        assert response.status_code == 200
        # Should complete within 30 seconds (adjust based on actual performance)
        assert duration < 30, f"Translation took too long: {duration:.2f}s"

    # ==================== Parameter Validation Tests ====================

    def test_empty_target_language(self, client):
        """Test with empty target language parameter."""
        response = client.post("/translate/?target_language=", json={"text": "Test"})

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_special_characters_in_language(self, client):
        """Test with special characters in language parameter."""
        response = client.post(
            "/translate/?target_language=english<script>", json={"text": "Test"}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_very_long_text(self, client):
        """Test with very long text (10000 chars)."""
        long_text = "A" * 10000
        response = client.post("/translate/", json={"text": long_text})

        # Should handle or reject gracefully
        assert response.status_code in [200, 400, 422]

    # ==================== Mock-Based Unit Tests ====================

    def test_translation_agent_initialization(self, client):
        """Test that translation agent is properly initialized."""
        with (
            patch("app.translation.get_settings") as mock_get_settings,
            patch("app.translation.get_chat_agent") as mock_get_chat_agent,
        ):
            mock_settings = MagicMock()
            mock_settings.translate_prompt_template = "Translate to {language}"
            mock_settings.translation_model = "test-model"
            mock_settings.translation_model_samplers = None
            mock_get_settings.return_value = mock_settings

            mock_agent = MagicMock()
            mock_result = MagicMock()
            mock_result.output = "Result"
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_get_chat_agent.return_value = mock_agent

            response = client.post("/translate/", json={"text": "Test"})

            assert response.status_code == 200
            mock_get_chat_agent.assert_called_once()
            mock_agent.run.assert_called_once()

    def test_translate_returns_correct_output(self, client):
        """Test that translation returns the correct output format."""
        # Note: This test verifies the response structure
        # The actual translation value is controlled by the fixture mocks
        response = client.post("/translate/", json={"text": "Input text"})

        assert response.status_code == 200
        assert "translated_text" in response.json()
        assert isinstance(response.json()["translated_text"], str)


class TestTranslationEndpointWithDirectMock:
    """Test suite with direct _translate_text mocking."""

    @pytest.fixture
    def client_with_direct_mock(self):
        """Create test client with direct _translate_text mock."""
        with patch("app.routes._translate_text") as mock_translate_text:
            # Direct mock of _translate_text in routes module
            mock_translate_text.return_value = "Expected translation"

            from app.routes import app

            client = TestClient(app, raise_server_exceptions=False)
            yield client

    def test_translate_calls_internal_function(self, client_with_direct_mock):
        """Test that endpoint calls the internal translation function."""
        from app import routes

        response = client_with_direct_mock.post("/translate/", json={"text": "Test"})

        assert response.status_code == 200
        # Verify the mock was called
        routes._translate_text.assert_called_once_with("Test", "english")

    def test_translate_with_various_languages(self, client_with_direct_mock):
        """Test translation with different target languages."""
        from app import routes

        languages = ["french", "german", "spanish", "japanese", "chinese"]

        for lang in languages:
            response = client_with_direct_mock.post(
                f"/translate/?target_language={lang}", json={"text": "Test"}
            )
            assert response.status_code == 200
            # Reset mock for next iteration
            routes._translate_text.reset_mock()

    def test_translate_returns_correct_output(self, client_with_direct_mock):
        """Test that translation returns the correct output format."""
        response = client_with_direct_mock.post(
            "/translate/", json={"text": "Input text"}
        )

        assert response.status_code == 200
        assert response.json()["translated_text"] == "Expected translation"
