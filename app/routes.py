import time

from fastapi import UploadFile, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.common import logger
from app.image_processing import _extract_labels_from_image
from app.translation import _translate_labels, _translate_text

# Configure CORS for Chrome extension and development
# Note: redirect_slashes=False prevents 307 redirects that break CORS preflight
app = FastAPI(redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - change for production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
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
async def root():
    """
    Root endpoint providing basic service information.
    :return: Service information
    """
    return {
        "service": "Image Annotator Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "translate": "/translate/",
            "annotate": "/image/annotate/",
        },
    }


@app.post("/translate/")
@app.post("/translate")
async def translate(request: TranslateRequest, target_language: str = "english"):
    """
    Post endpoint for text translation.
    This endpoint accepts a text string and translates it to the specified language.
    :param request: Request body containing the text to translate
    :param target_language: Target language for translation, defaults to 'english'
    :return: Translated text response
    """
    logger.info(f"Starting translation to {target_language}")
    start_time = time.perf_counter()

    translated_text = await _translate_text(request.text, target_language)

    total_duration = time.perf_counter() - start_time
    logger.info(f"Translation completed in {total_duration:.3f}s")
    return {"translated_text": translated_text}


@app.post("/image/annotate/")
@app.post("/image/annotate")
async def annotate(
    data: UploadFile, translate: bool = False, translate_language: str = "english"
):
    """
    Post endpoint for image annotation processing.
    This endpoint accepts an image file upload and optional translation parameters
    to process and annotate the image content. The annotation process can optionally
    include language translation of any text detected in the image.
    :param data: Uploaded image file to be annotated
    :param translate: Flag indicating whether to perform language translation on detected text
    :param translate_language: Target language for text translation, defaults to 'english'
    :return: Processed image annotation response
    """
    logger.info("Starting image annotation process")
    start_time = time.perf_counter()  # total processing start

    binary_image = await data.read()

    response = await _extract_labels_from_image(binary_image)

    # Step 2: Handle translation if requested
    if translate:
        translate_start = time.perf_counter()
        response.labels = await _translate_labels(response.labels, translate_language)
        translate_end = time.perf_counter()
        logger.info(f"Step 2 (translation) took {translate_end - translate_start:.3f}s")

    total_duration = time.perf_counter() - start_time
    logger.info(f"Image annotation process completed in {total_duration:.3f}s")
    return response
