"""Authentication routes for OAuth2 flow and access code management."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.access_code import AccessCodeManager
from app.auth.dependencies import require_auth
from app.container import get_access_code_manager

router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

# Create singleton access code manager
access_code_manager_instance = get_access_code_manager()


@router.get("/login")
async def login(
    request: Request,
    state: str = Query(..., description="CSRF state parameter"),
    access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
) -> RedirectResponse:
    """Redirect to OAuth2 provider for authentication.

    Generates PKCE code verifier and constructs authorization URL.
    The state parameter is passed through to protect against CSRF attacks.

    Args:
        request: The FastAPI request object.
        state: Random state string for CSRF protection.
        access_code_manager: The access code manager dependency.

    Returns:
        RedirectResponse to OAuth2 provider's authorization endpoint.

    Raises:
        HTTPException: If OAuth2 is not configured.
    """
    # Generate PKCE code verifier
    code_verifier = secrets.token_urlsafe(32)

    # Store code verifier in session (for callback validation if needed)
    # Note: For now, we don't validate the verifier since the OAuth2 client
    # handles it internally during token exchange
    request.session["pkce_verifier"] = code_verifier
    request.session["oauth2_state"] = state

    # Get authorization URL
    try:
        authorize_url = await access_code_manager._oauth2_client.get_authorize_url(
            redirect_uri=request.app.state.settings.oauth2_redirect_uri,
            state=state,
            code_verifier=code_verifier,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth2 not configured: {e}",
        ) from e

    return RedirectResponse(url=authorize_url)


@router.get("/callback", response_class=HTMLResponse)
async def callback(
    request: Request,
    code: str = Query(..., description="Authorization code from OAuth2 provider"),
    state: str = Query(..., description="State parameter from OAuth2 flow"),
    access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
) -> HTMLResponse:
    """Handle OAuth2 callback and display access code.

    Exchanges the authorization code for tokens, verifies the JWT,
    generates an access code, and displays it to the user.

    The access code is shown ONLY ONCE. Users must copy it to their
    browser extension settings.

    Args:
        request: The FastAPI request object.
        code: The authorization code from OAuth2 provider.
        state: The state parameter for CSRF validation.
        access_code_manager: The access code manager dependency.

    Returns:
        HTML page displaying the access code (shown once).
    """
    # Validate state parameter (CSRF protection)
    stored_state = request.session.get("oauth2_state")
    if stored_state and state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )
    
    # Get PKCE verifier before clearing session
    code_verifier = request.session.pop("pkce_verifier", None)
    if not code_verifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PKCE verifier not found in session",
        )
    
    # Clear session state after use
    request.session.pop("oauth2_state", None)
    try:
        # Handle callback and generate access code
        access_code = await access_code_manager.handle_callback(
            code=code,
            state=state,
            redirect_uri=request.app.state.settings.oauth2_redirect_uri,
            code_verifier=code_verifier,
        )

        # Render access code page
        return templates.TemplateResponse(
            "access_code.html",
            {
                "request": request,
                "access_code": access_code,
                "message": "Access code generated successfully. Copy this code to your browser extension settings.",
            },
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth2 flow failed: {e}",
        ) from e


@router.get("/access-code", response_class=HTMLResponse)
async def get_access_code(
    request: Request,
    user_id: str = Depends(require_auth),
    access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
) -> HTMLResponse:
    """Get or regenerate access code for authenticated user.

    This endpoint requires authentication. It shows the current access code
    or generates a new one if the user doesn't have one.

    Note: This can be called multiple times to regenerate the code.
    Each call invalidates the old code immediately.

    Args:
        request: The FastAPI request object.
        user_id: The authenticated user's ID (from require_auth dependency).
        access_code_manager: The access code manager dependency.

    Returns:
        HTML page displaying the access code.
    """
    # Get or generate access code
    access_code = await access_code_manager.get_code_for_user(user_id)
    if not access_code:
        access_code = await access_code_manager.regenerate_for_user(user_id)

    return templates.TemplateResponse(
        "access_code.html",
        {
            "request": request,
            "access_code": access_code,
            "message": "Your access code. Copy this to your browser extension settings. Click 'Regenerate' to create a new code (old code will be invalidated).",
            "show_regenerate": True,
        },
    )


@router.post("/access-code/regenerate")
async def regenerate_access_code(
    user_id: str = Depends(require_auth),
    access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
) -> dict:
    """Regenerate access code for authenticated user.

    Invalidates the old code immediately and returns a new one.
    This endpoint is useful for programmatic code regeneration.

    Args:
        user_id: The authenticated user's ID (from require_auth dependency).
        access_code_manager: The access code manager dependency.

    Returns:
        Dictionary containing the new access code.

    Raises:
        HTTPException: If regeneration fails.
    """
    try:
        access_code = await access_code_manager.regenerate_for_user(user_id)
        return {
            "access_code": access_code,
            "message": "Access code regenerated successfully. The old code has been invalidated.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate access code: {e}",
        ) from e
