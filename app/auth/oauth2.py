"""OAuth2/OIDC client with automatic discovery support."""

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

import httpx
from jose import jwt, jws, jwk
from jose.exceptions import JWTError

from app.config import Settings


@dataclass
class OAuth2Tokens:
    """Container for OAuth2 tokens."""

    access_token: str
    id_token: str
    token_type: str
    expires_in: int | None = None
    refresh_token: str | None = None


class OAuth2Client:
    """Generic OAuth2/OIDC client with automatic discovery support.

    Supports both OpenID Connect discovery (preferred) and manual endpoint configuration.
    When an issuer URL is provided, automatically fetches endpoints from
    .well-known/openid-configuration.

    Implements PKCE (Proof Key for Code Exchange) for enhanced security.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._http_client = httpx.AsyncClient()

        # OIDC discovery endpoints
        self._authorize_url: str | None = None
        self._token_url: str | None = None
        self._jwks_url: str | None = None
        self._issuer: str | None = None

        # Initialize endpoints from settings
        if settings.oauth2_issuer:
            self._issuer = settings.oauth2_issuer
        else:
            self._authorize_url = settings.oauth2_authorize_url
            self._token_url = settings.oauth2_token_url
            self._jwks_url = settings.oauth2_jwks_url

    async def _discover_endpoints(self) -> None:
        """Fetch and parse .well-known/openid-configuration.

        Discovers authorize, token, and JWKS endpoints from the OIDC discovery document.
        Validates that all endpoints use the same origin as the issuer.

        Raises:
            RuntimeError: If discovery fails or endpoints have mismatched origins.
        """
        if not self._issuer:
            raise RuntimeError("Cannot discover endpoints: no issuer configured")

        # Construct discovery URL
        issuer = self._issuer.rstrip("/")
        discovery_url = f"{issuer}/.well-known/openid-configuration"

        try:
            response = await self._http_client.get(
                discovery_url,
                timeout=10.0,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

            discovery_doc: dict[str, Any] = response.json()

            # Extract endpoints
            self._authorize_url = discovery_doc.get("authorization_endpoint")
            self._token_url = discovery_doc.get("token_endpoint")
            self._jwks_url = discovery_doc.get("jwks_uri")

            # Validate required endpoints
            if not all([self._authorize_url, self._token_url, self._jwks_url]):
                missing = []
                if not self._authorize_url:
                    missing.append("authorization_endpoint")
                if not self._token_url:
                    missing.append("token_endpoint")
                if not self._jwks_url:
                    missing.append("jwks_uri")
                raise RuntimeError(f"Discovery document missing endpoints: {', '.join(missing)}")

            # Validate origins match issuer
            issuer_origin = self._get_origin(issuer)
            for name, url in [
                ("authorize", self._authorize_url),
                ("token", self._token_url),
                ("jwks", self._jwks_url),
            ]:
                if url:
                    url_origin = self._get_origin(url)
                    if issuer_origin != url_origin:
                        raise RuntimeError(
                            f"Endpoint {name} origin ({url_origin}) does not match issuer origin ({issuer_origin})"
                        )

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to fetch OIDC discovery document: {e}") from e

    @staticmethod
    def _get_origin(url: str) -> str:
        """Extract origin (scheme + host + port) from URL."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _get_pkce_verifier(self) -> str:
        """Generate PKCE code verifier.

        Returns:
            Random 32-96 character string (uses 32 bytes = 256 bits).
        """
        return secrets.token_urlsafe(32)

    def _get_pkce_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier.

        Uses S256 method (SHA-256 hash).

        Args:
            verifier: The PKCE code verifier.

        Returns:
            Base64URL-encoded SHA-256 hash of the verifier.
        """
        # Hash the verifier
        hash_bytes = hashlib.sha256(verifier.encode()).digest()
        # Base64URL encode without padding
        return base64.urlsafe_b64encode(hash_bytes).rstrip(b"=").decode()

    async def exchange_code(self, code: str, redirect_uri: str, code_verifier: str | None = None) -> OAuth2Tokens:
        """Exchange authorization code for tokens.
        
        Exchanges the OAuth2 authorization code for access token and ID token.
        Performs OIDC discovery automatically if only issuer is configured.
        
        The ID token contains the JWT with user claims including `sub`.
        
        Args:
            code: The authorization code from OAuth2 provider.
            redirect_uri: The redirect URI used in the authorization request.
            code_verifier: The PKCE code verifier. If not provided, generates a new one.
        
        Returns:
            OAuth2Tokens containing access_token, id_token, token_type, etc.
        
        Raises:
            RuntimeError: If token exchange fails.
        """
        # Perform discovery if needed
        await self._ensure_discovered()
        
        if not self._token_url:
            raise RuntimeError("Token endpoint not configured")
        
        # Use provided verifier or generate new one
        if code_verifier is None:
            code_verifier = self._get_pkce_verifier()
        code_challenge = self._get_pkce_challenge(code_verifier)
        
        # Prepare token request
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._settings.oauth2_client_id,
            "client_secret": self._settings.oauth2_client_secret,
            "code_verifier": code_verifier,  # PKCE verifier
        }
        
        try:
            response = await self._http_client.post(
                self._token_url,
                data=data,
                timeout=10.0,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Token exchange failed: {e}") from e
        
        token_data: dict[str, Any] = response.json()
        
        return OAuth2Tokens(
            access_token=token_data["access_token"],
            id_token=token_data["id_token"],
            token_type=token_data["token_type"],
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token"),
        )

    async def verify_id_token(self, token: str) -> dict[str, Any]:
        """Verify JWT ID token using JWKS and extract claims.
        
        Fetches the public key from the provider's JWKS endpoint and verifies
        the token signature. Extracts and returns the token claims including `sub`.
        Performs OIDC discovery automatically if only issuer is configured.
        
        Args:
            token: The JWT ID token to verify.
        
        Returns:
            Decoded and verified token claims (including `sub` for user identification).
        
        Raises:
            RuntimeError: If verification fails or token is invalid.
        """
        # Perform discovery if needed
        await self._ensure_discovered()
        
        if not self._jwks_url:
            raise RuntimeError("JWKS URL not configured")
        
        try:
            # Fetch JWKS
            response = await self._http_client.get(
                self._jwks_url,
                timeout=10.0,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            jwks_data: dict[str, Any] = response.json()
            
            # Get token header to find key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            
            # Find matching key and construct it
            key = None
            for jwk_key in jwks_data.get("keys", []):
                if jwk_key.get("kid") == key_id or key_id is None:
                    try:
                        key = jwk.construct(jwk_key)
                        break
                    except Exception:
                        # If direct construction fails, try extracting from x5c
                        if "x5c" in jwk_key:
                            import base64
                            from cryptography.hazmat.primitives import serialization
                            from cryptography.hazmat.backends import default_backend
                            
                            # Extract certificate from x5c
                            cert_pem = base64.b64decode(jwk_key["x5c"][0])
                            public_key = serialization.load_pem_public_certificate(
                                cert_pem, backend=default_backend()
                            )
                            # Convert to PEM format for jose
                            key_pem = public_key.public_bytes(
                                encoding=serialization.Encoding.PEM,
                                format=serialization.PublicFormat.SubjectPublicKeyInfo,
                            )
                            # Load PEM key
                            from jose.backends import RSAKey
                            key = RSAKey(key=key_pem.decode())
                            break
            
            if not key:
                raise RuntimeError(f"No matching JWKS key found for kid: {key_id}")
            # Verify and decode token
            # Note: Disable at_hash verification since we don't use access_token here
            # The at_hash claim compares access_token hash, but we only need the ID token's sub claim
            claims = jwt.decode(
                token,
                key,
                algorithms=[unverified_header.get("alg", "RS256")],
                audience=self._settings.oauth2_client_id,
                options={
                    "verify_exp": True,
                    "verify_at_hash": False,  # Disable at_hash verification
                },
            )
            
            # Validate required claims
            if "sub" not in claims:
                raise RuntimeError("ID token missing required 'sub' claim")
            
            return claims
        except JWTError as e:
            raise RuntimeError(f"ID token verification failed: {e}") from e
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to fetch JWKS: {e}") from e

    async def _ensure_discovered(self) -> None:
        """Ensure endpoints are discovered if using OIDC discovery."""
        if self._issuer and not self._authorize_url:
            await self._discover_endpoints()

    async def get_authorize_url(self, redirect_uri: str, state: str, code_verifier: str) -> str:
        """Generate authorization URL with PKCE support.
        
        Constructs the OAuth2 authorization URL with PKCE code challenge.
        Performs OIDC discovery automatically if only issuer is configured.
        
        Args:
            redirect_uri: The redirect URI for OAuth2 callback.
            state: Random state string for CSRF protection.
            code_verifier: The PKCE code verifier (must match the one used to generate challenge).
        
        Returns:
            Authorization URL ready for browser redirect.
        
        Raises:
            RuntimeError: If authorize endpoint is not configured.
        """
        # Perform discovery if needed
        await self._ensure_discovered()
        
        if not self._authorize_url:
            raise RuntimeError("Authorize endpoint not configured")
        
        # Generate code challenge from verifier
        code_challenge = self._get_pkce_challenge(code_verifier)
        
        # Build query parameters
        from urllib.parse import urlencode
        
        params = {
            "response_type": "code",
            "client_id": self._settings.oauth2_client_id,
            "redirect_uri": redirect_uri,
            "scope": self._settings.oauth2_scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        
        return f"{self._authorize_url}?{urlencode(params)}"

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()
