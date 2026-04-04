"""Unit tests for authentication module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import secrets

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

class TestAccessCodeStore:
    """Tests for AccessCodeStore class."""

    @pytest.fixture
    def store(self):
        """Create a fresh AccessCodeStore for each test."""
        from app.auth.store import AccessCodeStore
        return AccessCodeStore()

    def test_generate_code_creates_new_code(self, store):
        """Test that generate_code creates a new cryptographically secure code."""
        user_id = "user-123"
        code = store.generate_code(user_id)

        assert code is not None
        assert isinstance(code, str)
        assert len(code) >= 40  # URL-safe base64 encoded 32 bytes

    def test_1_1_mapping_invalidates_old_code(self, store):
        """Test that generating a new code invalidates the old one (1:1 mapping)."""
        user_id = "user-123"
        
        # Generate first code
        code1 = store.generate_code(user_id)
        
        # Generate second code
        code2 = store.generate_code(user_id)
        
        # Old code should be invalid
        assert store.validate_code(code1) is None
        
        # New code should be valid
        assert store.validate_code(code2) == user_id

    def test_validate_code_returns_user_id(self, store):
        """Test that validate_code returns the correct user_id."""
        user_id = "user-123"
        code = store.generate_code(user_id)

        assert store.validate_code(code) == user_id

    def test_validate_code_returns_none_for_invalid_code(self, store):
        """Test that validate_code returns None for invalid codes."""
        assert store.validate_code("invalid-code") is None

    def test_get_code_for_user(self, store):
        """Test getting current code for a user."""
        user_id = "user-123"
        code = store.generate_code(user_id)

        assert store.get_code_for_user(user_id) == code

    def test_get_code_for_user_returns_none_when_no_code(self, store):
        """Test that get_code_for_user returns None for users without codes."""
        assert store.get_code_for_user("nonexistent-user") is None

    def test_regenerate_code(self, store):
        """Test regenerating code for a user."""
        user_id = "user-123"
        code1 = store.generate_code(user_id)
        code2 = store.regenerate_code(user_id)

        assert code1 != code2
        assert store.validate_code(code1) is None
        assert store.validate_code(code2) == user_id

    def test_remove_user(self, store):
        """Test removing a user and their code."""
        user_id = "user-123"
        code = store.generate_code(user_id)

        assert store.remove_user(user_id) is True
        assert store.validate_code(code) is None
        assert store.get_code_for_user(user_id) is None

    def test_remove_user_returns_false_when_not_exists(self, store):
        """Test that remove_user returns False for non-existent users."""
        assert store.remove_user("nonexistent-user") is False


class TestAccessCodeManager:
    """Tests for AccessCodeManager class."""

    @pytest.fixture
    def mock_oauth2_client(self):
        """Create a mock OAuth2 client."""
        mock = AsyncMock()
        mock.exchange_code = AsyncMock()
        mock.verify_id_token = AsyncMock()
        return mock

    @pytest.fixture
    def store(self):
        """Create a fresh AccessCodeStore."""
        from app.auth.store import AccessCodeStore
        return AccessCodeStore()

    @pytest.fixture
    def manager(self, store, mock_oauth2_client):
        """Create an AccessCodeManager with mocked dependencies."""
        from app.auth.access_code import AccessCodeManager
        return AccessCodeManager(store, mock_oauth2_client)

    @pytest.mark.asyncio
    async def test_handle_callback_generates_code(self, manager, mock_oauth2_client, store):
        """Test that handle_callback generates an access code after OAuth2 flow."""
        # Mock OAuth2 response
        mock_tokens = MagicMock()
        mock_tokens.id_token = "mock-id-token"
        mock_oauth2_client.exchange_code.return_value = mock_tokens
        mock_oauth2_client.verify_id_token.return_value = {"sub": "user-123"}

        # Mock request object
        mock_request = MagicMock()

        # Handle callback
        access_code = await manager.handle_callback(
            code="auth-code",
            state="state",
            redirect_uri="http://localhost/callback",
            request=mock_request
        )

        # Verify OAuth2 calls
        mock_oauth2_client.exchange_code.assert_called_once()
        mock_oauth2_client.verify_id_token.assert_called_once()

        # Verify access code was generated
        assert access_code is not None
        assert store.validate_code(access_code) == "user-123"

    @pytest.mark.asyncio
    async def test_validate_returns_user_id(self, manager, store):
        """Test that validate returns user_id for valid code."""
        user_id = "user-123"
        code = store.generate_code(user_id)

        result = await manager.validate(code)
        assert result == user_id

    @pytest.mark.asyncio
    async def test_validate_returns_none_for_invalid_code(self, manager):
        """Test that validate returns None for invalid code."""
        result = await manager.validate("invalid-code")
        assert result is None

    @pytest.mark.asyncio
    async def test_regenerate_for_user(self, manager, store):
        """Test regenerating code for a user."""
        user_id = "user-123"
        code1 = store.generate_code(user_id)
        code2 = await manager.regenerate_for_user(user_id)

        assert code1 != code2
        assert store.validate_code(code1) is None
        assert store.validate_code(code2) == user_id


class TestRequireAuth:
    """Tests for require_auth dependency."""

    @pytest.fixture
    def mock_access_code_manager(self):
        """Create a mock access code manager."""
        mock = AsyncMock()
        mock.validate = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_require_auth_with_valid_code(self, mock_access_code_manager):
        """Test require_auth with valid access code."""
        from app.auth.dependencies import require_auth

        mock_access_code_manager.validate.return_value = "user-123"

        result = await require_auth(
            x_auth_code="valid-code",
            access_code_manager=mock_access_code_manager
        )

        assert result == "user-123"

    @pytest.mark.asyncio
    async def test_require_auth_without_code(self, mock_access_code_manager):
        """Test require_auth raises 401 when code is missing."""
        from app.auth.dependencies import require_auth
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await require_auth(
                x_auth_code=None,
                access_code_manager=mock_access_code_manager
            )

        assert exc_info.value.status_code == 401
        assert "Missing X-Auth-Code header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_auth_with_invalid_code(self, mock_access_code_manager):
        """Test require_auth raises 401 when code is invalid."""
        from app.auth.dependencies import require_auth
        from fastapi import HTTPException

        mock_access_code_manager.validate.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await require_auth(
                x_auth_code="invalid-code",
                access_code_manager=mock_access_code_manager
            )

        assert exc_info.value.status_code == 401
        assert "Invalid or expired access code" in exc_info.value.detail


class TestOAuth2Client:
    """Tests for OAuth2Client class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        from app.config import Settings
        
        # Create minimal settings for testing
        settings = MagicMock(spec=Settings)
        settings.oauth2_issuer = "https://keycloak.example.com/realms/test"
        settings.oauth2_client_id = "test-client"
        settings.oauth2_client_secret = "test-secret"
        settings.oauth2_redirect_uri = "http://localhost/callback"
        settings.oauth2_scopes = "openid profile email"
        settings.oauth2_authorize_url = None
        settings.oauth2_token_url = None
        settings.oauth2_jwks_url = None
        
        return settings

    @pytest.fixture
    def oauth2_client(self, mock_settings):
        """Create an OAuth2Client with mocked settings."""
        from app.auth.oauth2 import OAuth2Client
        return OAuth2Client(mock_settings)

    def test_get_pkce_verifier(self, oauth2_client):
        """Test PKCE verifier generation."""
        verifier = oauth2_client._get_pkce_verifier()
        
        assert verifier is not None
        assert len(verifier) >= 43  # URL-safe base64 encoded 32 bytes

    def test_get_pkce_challenge(self, oauth2_client):
        """Test PKCE challenge generation."""
        verifier = secrets.token_urlsafe(32)
        challenge = oauth2_client._get_pkce_challenge(verifier)
        
        assert challenge is not None
        assert isinstance(challenge, str)
        # Challenge is SHA-256 hash (32 bytes) base64url encoded = 43 chars
        assert len(challenge) == 43
    @pytest.mark.asyncio
    async def test_get_authorize_url(self):
        """Test authorization URL generation."""
        # Create settings with manual endpoints (no discovery)
        from app.config import Settings
        from app.auth.oauth2 import OAuth2Client
        
        settings = MagicMock(spec=Settings)
        settings.oauth2_issuer = None  # Disable discovery
        settings.oauth2_authorize_url = "https://keycloak.example.com/auth"
        settings.oauth2_token_url = "https://keycloak.example.com/token"
        settings.oauth2_jwks_url = "https://keycloak.example.com/jwks"
        settings.oauth2_client_id = "test-client"
        settings.oauth2_client_secret = "test-secret"
        settings.oauth2_redirect_uri = "http://localhost/callback"
        settings.oauth2_scopes = "openid profile email"
        
        # Create client with manual endpoints
        client = OAuth2Client(settings)
        
        redirect_uri = "http://localhost/callback"
        state = "random-state"
        code_verifier = secrets.token_urlsafe(32)
        
        url = await client.get_authorize_url(redirect_uri, state, code_verifier)
        
        assert "https://keycloak.example.com/auth" in url
        assert "response_type=code" in url
        assert f"client_id={settings.oauth2_client_id}" in url
        assert "redirect_uri=" in url  # URL is encoded
        assert "state=" in url
        assert "code_challenge=" in url
        assert "code_challenge_method=S256" in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
