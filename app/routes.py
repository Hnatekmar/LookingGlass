import io
import time

from PIL import Image
from fastapi import UploadFile, FastAPI
from app.image_processing import _extract_labels_from_image, _extract_labels_from_bounding_boxes
from app.schema import AnnotationResponse
from app.translation import _translate_labels
from app.common import logger
app = FastAPI()

@app.post("/image/annotate/")
async def annotate(data: UploadFile, translate: bool = False, translate_language: str = "english"):
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
