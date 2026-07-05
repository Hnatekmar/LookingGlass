# Import OS module for environment variable handling
import os
from app.config import get_settings
from app import app
from app.common import logger

# Import Uvicorn to run the ASGI application server
import uvicorn


# Add startup event to print configuration
@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("Application Starting - Configuration Summary")
    logger.info("=" * 60)
    logger.info(f"Image Model: {settings.image_model}")
    logger.info(f"Translation Model: {settings.translation_model}")
    logger.info(f"Image Model URL: {settings.image_model_url}")
    logger.info(f"Translation Model URL: {settings.translation_model_url}")
    logger.info(f"Canvas Dimensions: {settings.canvas_width}x{settings.canvas_height}")
    logger.info(f"Default Translation Language: {settings.default_translate_language}")
    logger.info("=" * 60)


# Entry point: start the FastAPI app with Uvicorn
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
