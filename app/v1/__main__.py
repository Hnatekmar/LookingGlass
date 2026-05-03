"""FastAPI application with version 1 API routes."""

import logging
import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.v1 import auth, image, translate

logger = logging.getLogger(__name__)

settings = get_settings()

# Configure CORS for Chrome extension and development
# Note: redirect_slashes=False prevents 307 redirects that break CORS preflight
app = FastAPI(redirect_slashes=False)

# Templates for HTML pages
templates = Jinja2Templates(directory="app/templates")

# Store settings in app state for access by auth routes
app.state.settings = settings

# Add session middleware for OAuth2 state management
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - change for production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["X-Auth-Code"],
)


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
            "auth": "/v1/auth/",
        },
    }


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_redirect(request: Request):
    """
    Show login page at root path.
    """
    state = secrets.token_urlsafe(16)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "state": state}
    )


# Include versioned routers
app.include_router(auth.router, prefix="/v1")
app.include_router(translate.router, prefix="/v1")
app.include_router(image.router, prefix="/v1")