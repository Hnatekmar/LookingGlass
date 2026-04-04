"""Authentication dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.auth.access_code import AccessCodeManager
from app.container import get_access_code_manager


async def require_auth(
    x_auth_code: str | None = Header(
        None, alias="X-Auth-Code", description="Access code from browser extension"
    ),
    access_code_manager: AccessCodeManager = Depends(get_access_code_manager),
) -> str:
    """Dependency that requires valid authentication.

    Extracts and validates the access code from the X-Auth-Code header.
    Returns the user_id on success.

    Args:
        x_auth_code: The access code from the X-Auth-Code header.
        access_code_manager: The access code manager for validation.

    Returns:
        The authenticated user's ID.

    Raises:
        HTTPException: If authentication fails (401 Unauthorized).
    """

    if x_auth_code is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Auth-Code header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = await access_code_manager.validate(x_auth_code)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access code",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(
    x_auth_code: str | None = Header(None, alias="X-Auth-Code"),
    access_code_manager: AccessCodeManager = Depends(get_access_code_manager),
) -> str | None:
    """Optional dependency that returns user_id if authenticated, None otherwise.

    Use this for endpoints that have optional authentication.

    Args:
        x_auth_code: The access code from the X-Auth-Code header.
        access_code_manager: The access code manager for validation.

    Returns:
        The user_id if authenticated, None otherwise.
    """
    if x_auth_code is None:
        return None

    user_id = await access_code_manager.validate(x_auth_code)
    return user_id  # Returns None if code is invalid
