"""FastAPI application with version 1 API routes.

Note: Configuration values (API_KEY, CORS_ORIGINS) are read at import time.
Changes to environment variables require a process restart to take effect.
"""

import hmac
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.v1 import image, translate

logger = logging.getLogger(__name__)

# Configure CORS for the browser extension and development
# Note: redirect_slashes=False prevents 307 redirects that break CORS preflight
# Security: In production, restrict allow_origins to the actual extension origin
# instead of "*" when allow_credentials=True.
app = FastAPI(redirect_slashes=False)

_settings = get_settings()

# Parse CORS origins from Settings
_cors_origins_str = _settings.cors_origins
_cors_origins = [o.strip() for o in _cors_origins_str.split(",") if o.strip()]
# If the parsed origin list is empty (e.g. misconfigured as ","), fall back to "*"
if not _cors_origins:
    if _cors_origins_str.strip() and _cors_origins_str.strip() != "*":
        logger.warning(
            "CORS_ORIGINS='%s' produced an empty origin list after parsing; "
            "falling back to '*' (wide open). Check your CORS_ORIGINS configuration.",
            _cors_origins_str,
        )
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=(_cors_origins != ["*"]),
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["X-Auth-Code"],
)

# Optional API key authentication middleware
# Read from Settings (which sources from API_KEY env var)
# Note: Read once at import time; requires restart to pick up changes.
_API_KEY = _settings.api_key


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Check API key on all routes except health check if API_KEY is configured.

    Uses constant-time comparison to mitigate timing attacks.
    """
    if _API_KEY and request.url.path != "/v1/health":
        api_key = request.headers.get("X-API-Key")
        if not api_key or not hmac.compare_digest(api_key, _API_KEY):
            return HTMLResponse(
                content='{"detail":"Unauthorized"}',
                status_code=401,
                headers={"Content-Type": "application/json"},
            )
    response = await call_next(request)
    return response


@app.get("/v1/health")
async def health_check():
    """
    Health check endpoint for monitoring and connection testing.
    Returns the current status of the backend service.
    :return: Health status response
    """
    return {
        "status": "healthy",
        "service": "Image Annotator Backend",
        "version": "1.0.0",
    }


@app.get("/v1/")
async def root():
    """
    Root endpoint providing service information.
    :return: Service info response
    """
    return {
        "service": "Image Annotator Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/v1/health",
            "translate": "/v1/translate/",
            "annotate": "/v1/image/annotate/",
            "annotate_stream": "/v1/image/annotate/stream",
        },
    }


# Include versioned routers
app.include_router(translate.router, prefix="/v1")
app.include_router(image.router, prefix="/v1")
