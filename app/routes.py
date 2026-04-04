import time
import secrets
from urllib.parse import urlencode

from fastapi import UploadFile, FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.common import logger
from app.image_processing import _extract_labels_from_image
from app.translation import _translate_labels, _translate_labels_batch, _translate_text
from app.auth.dependencies import require_auth
from app.auth.access_code import AccessCodeManager
from app.container import get_access_code_manager

# Create singleton access code manager for routes
access_code_manager_instance = get_access_code_manager()
# Import settings
from app.config import get_settings

# Configure CORS for Chrome extension and development
# Note: redirect_slashes=False prevents 307 redirects that break CORS preflight
app = FastAPI(redirect_slashes=False)

# Store settings in app state for access by auth routes
settings = get_settings()
app.state.settings = settings

# Add session middleware for OAuth2 state management
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - change for production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["X-Auth-Code"],
)

class TranslateRequest(BaseModel):
    text: str


@app.get("/health")
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


@app.get("/")
async def root(request: Request):
    """
    Root endpoint providing a login page and service information.
    :return: HTML login page or service info
    """
    # Check if OAuth2 is configured
    settings = get_settings()
    if not settings.oauth2_issuer:
        return {
            "service": "Image Annotator Backend",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "translate": "/translate/",
                "annotate": "/image/annotate/",
                "login": "/auth/login",
            },
            "message": "OAuth2 not configured. Visit /auth/login?state=<state> to authenticate.",
        }

    # Generate state parameter and redirect to login
    import secrets
    state = secrets.token_urlsafe(32)
    return RedirectResponse(url=f"/auth/login?state={state}")



@app.post("/translate/")
@app.post("/translate")
async def translate(
    request: TranslateRequest,
    target_language: str = "english",
    user_id: str = Depends(require_auth),
    _access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
):
    """
    Post endpoint for text translation.
    This endpoint accepts a text string and translates it to the specified language.
    Requires valid authentication via X-Auth-Code header.
    :param request: Request body containing the text to translate
    :param target_language: Target language for translation, defaults to 'english'
    :param user_id: Authenticated user ID (from require_auth dependency)
    :param _access_code_manager: Access code manager dependency
    :return: Translated text response
    """
    logger.info(f"Starting translation to {target_language} for user {user_id}")
    start_time = time.perf_counter()

    translated_text = await _translate_text(request.text, target_language)

    total_duration = time.perf_counter() - start_time
    logger.info(f"Translation completed in {total_duration:.3f}s")
    return {"translated_text": translated_text}


@app.post("/image/annotate/")
@app.post("/image/annotate")
async def annotate(
    data: UploadFile,
    translate: bool = False,
    translate_language: str = "english",
    user_id: str = Depends(require_auth),
    _access_code_manager: AccessCodeManager = Depends(lambda: access_code_manager_instance),
):
    """
    Post endpoint for image annotation processing.
    This endpoint accepts an image file upload and optional translation parameters
    to process and annotate the image content. The annotation process can optionally
    include language translation of any text detected in the image.
    Requires valid authentication via X-Auth-Code header.
    :param data: Uploaded image file to be annotated
    :param translate: Flag indicating whether to perform language translation on detected text
    :param translate_language: Target language for text translation, defaults to 'english'
    :param user_id: Authenticated user ID (from require_auth dependency)
    :param _access_code_manager: Access code manager dependency
    :return: Processed image annotation response
    """
    logger.info(f"Starting image annotation process for user {user_id}")
    start_time = time.perf_counter()  # total processing start

    binary_image = await data.read()

    response = await _extract_labels_from_image(binary_image)

    # Step 2: Handle translation if requested
    if translate:
        translate_start = time.perf_counter()
        # Use batch translation for efficiency (single request instead of N parallel requests)
        response.labels = await _translate_labels_batch(
            response.labels, translate_language
        )
        translate_end = time.perf_counter()
        logger.info(
            f"Step 2 (batch translation) took {translate_end - translate_start:.3f}s"
        )

    total_duration = time.perf_counter() - start_time
    logger.info(f"Image annotation process completed in {total_duration:.3f}s")
    return response



# Include authentication routes
from app.auth_routes import router as auth_router
app.include_router(auth_router)