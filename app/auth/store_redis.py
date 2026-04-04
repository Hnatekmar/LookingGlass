"""Redis-backed access code store for production deployments."""

import logging
import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis.asyncio as redis

from .store import AccessCodeStore

logger = logging.getLogger(__name__)


class RedisAccessCodeStore(AccessCodeStore):
    """Redis-backed access code store with 1:1 user-to-code mapping.

    Each user can have exactly one active access code at a time.
    When a new code is generated for a user, the old code is immediately invalidated.

    Features:
    - Persistent storage across application restarts
    - Shared state across multiple backend replicas
    - Configurable TTL for access codes (default: 24 hours)
    - Atomic operations using Redis transactions

    Key format:
    - access_code:{code} -> user_id (TTL: access_code_ttl)
    - user_code:{user_id} -> code (TTL: access_code_ttl)
    """

    def __init__(
        self,
        redis_client: "redis.Redis",
        key_prefix: str = "access_code",
        ttl: int = 86400,  # 24 hours default
    ) -> None:
        """Initialize Redis access code store.

        Args:
            redis_client: Async Redis client instance.
            key_prefix: Prefix for Redis keys to avoid collisions.
            ttl: Time-to-live for access codes in seconds (default: 86400 = 24h).
        """
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._ttl = ttl

    def _make_code_key(self, code: str) -> str:
        """Create Redis key for access code."""
        return f"{self._key_prefix}:code:{code}"

    def _make_user_key(self, user_id: str) -> str:
        """Create Redis key for user's current code."""
        return f"{self._key_prefix}:user:{user_id}"

    def generate_code(self, user_id: str) -> str:
        """Generate new access code for user.

        If user already has a code, the old code is invalidated (1:1 mapping).
        Uses Redis transaction for atomic read-modify-write.

        Args:
            user_id: The unique user identifier (from JWT `sub` claim).

        Returns:
            The newly generated access code (cryptographically secure 256-bit random bytes).
        """
        # Generate cryptographically secure random code (32 bytes = 256 bits)
        code = secrets.token_urlsafe(32)

        # Use pipeline for atomic operation
        # This ensures we:
        # 1. Get old code for user (if any)
        # 2. Delete old code mapping
        # 3. Set new code mappings with TTL
        pipe = self._redis.pipeline(transaction=True)

        try:
            # Watch the user key for changes
            pipe.watch(self._make_user_key(user_id))

            # Get old code if exists
            old_code_key = self._make_user_key(user_id)
            old_code = pipe.get(old_code_key)

            # Start transaction
            pipe.multi()

            # If old code exists, remove its mapping
            if old_code:
                pipe.delete(self._make_code_key(old_code.decode()))

            # Set new mappings with TTL
            code_key = self._make_code_key(code)
            pipe.setex(code_key, self._ttl, user_id)
            pipe.setex(old_code_key, self._ttl, code)

            # Execute transaction
            pipe.execute()

            logger.debug(f"Generated new access code for user {user_id}")
            return code

        except Exception as e:
            logger.error(f"Failed to generate access code for user {user_id}: {e}")
            raise RuntimeError(f"Failed to generate access code: {e}") from e

    def validate_code(self, code: str) -> str | None:
        """Validate access code and return user_id.

        Args:
            code: The access code to validate.

        Returns:
            The user_id if code is valid, None if invalid or expired.
            Returns None on Redis errors (fail closed).
        """
        try:
            user_id = self._redis.get(self._make_code_key(code))
            return user_id.decode() if user_id else None
        except Exception as e:
            logger.error(f"Failed to validate access code: {e}")
            # Fail closed: return None on error
            return None

    def get_code_for_user(self, user_id: str) -> str | None:
        """Get current access code for user.

        Args:
            user_id: The unique user identifier.

        Returns:
            The current access code, or None if user has no code.
        """
        try:
            code = self._redis.get(self._make_user_key(user_id))
            return code.decode() if code else None
        except Exception as e:
            logger.error(f"Failed to get code for user {user_id}: {e}")
            return None

    def regenerate_code(self, user_id: str) -> str:
        """Regenerate access code for user.

        Invalidates the old code immediately and returns a new one.

        Args:
            user_id: The unique user identifier.

        Returns:
            The newly generated access code.
        """
        return self.generate_code(user_id)

    def remove_user(self, user_id: str) -> bool:
        """Remove user and their access code.

        Args:
            user_id: The unique user identifier.

        Returns:
            True if user existed and was removed, False otherwise.
        """
        try:
            # Get old code first
            old_code = self._redis.get(self._make_user_key(user_id))

            if not old_code:
                return False

            # Delete both keys
            pipe = self._redis.pipeline(transaction=True)
            pipe.delete(self._make_user_key(user_id))
            pipe.delete(self._make_code_key(old_code.decode()))
            pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Failed to remove user {user_id}: {e}")
            return False
