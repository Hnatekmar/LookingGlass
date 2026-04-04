"""Access code manager for OAuth2-based access code lifecycle."""

from typing import TYPE_CHECKING

from app.auth.store import AccessCodeStore
from app.auth.oauth2 import OAuth2Client

if TYPE_CHECKING:
    from fastapi import Request


class AccessCodeManager:
    """Manages access code lifecycle with 1:1 user-to-code mapping.

    Coordinates OAuth2 authentication flow with access code generation.
    Handles the complete flow from OAuth2 callback to access code issuance.

    Features:
    - 1:1 mapping between user and access code
    - Automatic code invalidation on regeneration
    - OAuth2 code exchange and JWT verification
    - Access code validation for API requests
    """

    def __init__(self, store: AccessCodeStore, oauth2_client: OAuth2Client) -> None:
        """Initialize access code manager.

        Args:
            store: The access code store for code management.
            oauth2_client: The OAuth2 client for token exchange and verification.
        """
        self._store = store
        self._oauth2_client = oauth2_client

    async def handle_callback(
        self, code: str, state: str, redirect_uri: str, code_verifier: str,
    ) -> str:
        """Handle OAuth2 callback: exchange code, verify JWT, generate access code.
        
        This is the main entry point for the OAuth2 flow. It:
        1. Exchanges the authorization code for tokens
        2. Verifies the ID token and extracts user identity
        3. Generates a new access code for the user (invalidating old one if exists)
        4. Returns the access code to be displayed to the user
        
        Args:
            code: The authorization code from OAuth2 provider.
            state: The state parameter (for CSRF validation if implemented).
            redirect_uri: The redirect URI used in authorization request.
            code_verifier: The PKCE code verifier from the session.
        
        Returns:
            The newly generated access code.
        
        Raises:
            RuntimeError: If token exchange or verification fails.
        """
        # Exchange authorization code for tokens
        tokens = await self._oauth2_client.exchange_code(code, redirect_uri, code_verifier)
        
        # Verify ID token and extract claims
        claims = await self._oauth2_client.verify_id_token(tokens.id_token)
        
        # Extract user identity from JWT `sub` claim
        user_id = claims["sub"]
        
        # Generate access code for user (1:1 mapping - old code invalidated)
        access_code = self._store.generate_code(user_id)
        
        return access_code
    async def validate(self, code: str) -> str | None:
        """Validate access code and return user_id.

        Args:
            code: The access code to validate.

        Returns:
            The user_id if code is valid, None if invalid or expired.
        """
        return self._store.validate_code(code)

    async def regenerate_for_user(self, user_id: str) -> str:
        """Regenerate access code for authenticated user.

        Invalidates the old code immediately and returns a new one.
        This should only be called for authenticated users.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            The newly generated access code.
        """
        return self._store.regenerate_code(user_id)

    async def get_code_for_user(self, user_id: str) -> str | None:
        """Get current access code for user.

        Args:
            user_id: The user's ID.

        Returns:
            The current access code, or None if user has no code.
        """
        return self._store.get_code_for_user(user_id)

    async def remove_user(self, user_id: str) -> bool:
        """Remove user and their access code.

        Args:
            user_id: The user's ID.

        Returns:
            True if user existed and was removed, False otherwise.
        """
        return self._store.remove_user(user_id)
