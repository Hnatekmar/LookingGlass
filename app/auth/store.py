"""Access code store with 1:1 user-to-code mapping."""

from abc import ABC, abstractmethod
import secrets


class AccessCodeStore(ABC):
    """Abstract base class for access code stores."""

    @abstractmethod
    def generate_code(self, user_id: str) -> str:
        """Generate new access code for user."""
        pass

    @abstractmethod
    def validate_code(self, code: str) -> str | None:
        """Validate access code and return user_id, or None if invalid."""
        pass

    @abstractmethod
    def get_code_for_user(self, user_id: str) -> str | None:
        """Get current access code for user, or None if not found."""
        pass

    @abstractmethod
    def regenerate_code(self, user_id: str) -> str:
        """Regenerate access code for user, invalidating the old one."""
        pass

    @abstractmethod
    def remove_user(self, user_id: str) -> bool:
        """Remove user and their access code. Returns True if user existed."""
        pass


class InMemoryAccessCodeStore(AccessCodeStore):
    """In-memory store for access codes with 1:1 user-to-code mapping.

    Each user can have exactly one active access code at a time.
    When a new code is generated for a user, the old code is immediately invalidated.

    Note: This is an in-memory store. Codes are lost on application restart.
    For production deployments with multiple replicas, use RedisAccessCodeStore.
    """

    def __init__(self) -> None:
        self._user_to_code: dict[str, str] = {}
        self._code_to_user: dict[str, str] = {}

    def generate_code(self, user_id: str) -> str:
        """Generate new access code for user.

        If user already has a code, the old code is invalidated (1:1 mapping).

        Args:
            user_id: The unique user identifier (from JWT `sub` claim).

        Returns:
            The newly generated access code (cryptographically secure 256-bit random bytes).
        """
        # Remove old code if user already has one
        if user_id in self._user_to_code:
            old_code = self._user_to_code[user_id]
            del self._code_to_user[old_code]

        # Generate cryptographically secure random code (32 bytes = 256 bits)
        code = secrets.token_urlsafe(32)

        # Store bidirectional mapping
        self._user_to_code[user_id] = code
        self._code_to_user[code] = user_id

        return code

    def validate_code(self, code: str) -> str | None:
        """Validate access code and return user_id.

        Args:
            code: The access code to validate.

        Returns:
            The user_id if code is valid, None if invalid or has been regenerated.
        """
        return self._code_to_user.get(code)

    def get_code_for_user(self, user_id: str) -> str | None:
        """Get current access code for user.

        Args:
            user_id: The unique user identifier.

        Returns:
            The current access code, or None if user has no code.
        """
        return self._user_to_code.get(user_id)

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
        if user_id not in self._user_to_code:
            return False

        old_code = self._user_to_code[user_id]
        del self._user_to_code[user_id]
        del self._code_to_user[old_code]

        return True
