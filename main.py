import asyncio
import io
import logging
from typing import List, Tuple

import cv2
from PIL import Image, ImageOps
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings, BinaryContent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import time

IMAGE_MODEL = "qwen3-8b-instruct"
TRANSLATION_MODEL = "gpt-oss"
LABEL_PROMPT = """
You are a text region detection agent for machine translation workflows.

**Task:** Identify and localize all text regions in the input image.

**Input:** A single image containing text (e.g., speech bubbles, paragraphs, captions, signs).

**Output Requirements:**
- Return a list of bounding boxes, one for each distinct text region
- Each bounding box must use normalized coordinates in the format:
  - x1, y1: top-left corner coordinates
  - x2, y2: bottom-right corner coordinates
  - All coordinates are normalized to a 0-1000 scale 

**Detection Guidelines:**
- Detect ALL visible text in the image, including:
  - Speech bubbles and dialogue text
  - Paragraphs and continuous text blocks
  - Signs, labels, and captions
  - Overlaid text and watermarks
- Each text region should have its own separate bounding box
- Bounding boxes should tightly fit around the text with minimal padding
- Group text that logically belongs together (e.g., text within the same speech bubble)
- Do not overlap bounding boxes unless text regions actually overlap in the image
"""

qwen3_instruct_sampler = ModelSettings(
    temperature=0.7,
    extra_body={
        "top_p": 0.8,
        "top_k": 20,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
        "max_tokens": 32768
    }
)

qwen3_thinking_sampler = ModelSettings(
    temperature=0.6,
    extra_body={
        "top_p": 0.95,
        "top_k": 20,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0,
        "max_tokens": 40960
    }
)


image_model_samplers =  qwen3_instruct_sampler

translation_model_samplers = None # qwen3_instruct_sampler
#     ModelSettings(
#     # temperature=0.6,
#     # extra_body={
#     #     "top_p": 0.95,
#     #     "top_k": 20,
#     #     "presence_penalty": 0.0,
#     #     "repetition_penalty": 1.0,
#     #     "max_tokens": 40960
#     # }
# ))


# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger instance
logger = logging.getLogger(__name__)
app = FastAPI()


class Label(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    text: str

class TextBoundingBox(BaseModel):
    bbox_2d: List[float]  # [x1, y1, x2, y2] format
    text: str

class TextBoundingBoxContainer(BaseModel):
    labels: List[TextBoundingBox]

class CoordinateMapping(BaseModel):
    """Contains information for transforming coordinates back to original image scale"""
    original_width: int
    original_height: int
    canvas_width: int
    canvas_height: int
    scale_x: float
    scale_y: float
    offset_x: int
    offset_y: int

class AnnotationResponse(BaseModel):
    labels: List[Label]
    coordinate_mapping: CoordinateMapping = None

def transform_coordinates_to_original(
    bbox_2d: List[float], 
    mapping: CoordinateMapping
) -> List[float]:
    """Transform coordinates from canvas back to original image scale (0-1000)"""
    if mapping is None:
        return bbox_2d
    
    # Get canvas coordinates
    x1_canvas = bbox_2d[0]
    y1_canvas = bbox_2d[1]
    x2_canvas = bbox_2d[2]
    y2_canvas = bbox_2d[3]
    
    # Subtract offset to get coordinates relative to the scaled image
    x1_scaled = x1_canvas - mapping.offset_x
    y1_scaled = y1_canvas - mapping.offset_y
    x2_scaled = x2_canvas - mapping.offset_x
    y2_scaled = y2_canvas - mapping.offset_y
    
    # Clamp to scaled image bounds
    x1_scaled = max(0, min(x1_scaled, mapping.canvas_width))
    y1_scaled = max(0, min(y1_scaled, mapping.canvas_height))
    x2_scaled = max(0, min(x2_scaled, mapping.canvas_width))
    y2_scaled = max(0, min(y2_scaled, mapping.canvas_height))
    
    # Transform to original coordinates
    x1_original = max(0, min(999, (x1_scaled / mapping.scale_x) / mapping.original_width * 1000))
    y1_original = max(0, min(999, (y1_scaled / mapping.scale_y) / mapping.original_height * 1000))
    x2_original = max(0, min(999, (x2_scaled / mapping.scale_x) / mapping.original_width * 1000))
    y2_original = max(0, min(999, (y2_scaled / mapping.scale_y) / mapping.original_height * 1000))
    
    # Ensure proper ordering
    return [min(x1_original, x2_original), min(y1_original, y2_original), 
            max(x1_original, x2_original), max(y1_original, y2_original)]

def build_chat_agent(url: str, model: str, prompt: str, output_type=AnnotationResponse, settings=ModelSettings(
    temperature=0.6,
    extra_body={
        "top_p": 0.95,
        "top_k": 20,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0
    }
)) -> Agent:
    # Create a custom SSL context to prevent SSL errors
    chat_model = OpenAIChatModel(
        model_name=model,
        provider=OpenAIProvider(
            base_url=url,
        )
    )
    agent = Agent(
        model=chat_model,
        retries=32,
        system_prompt=prompt,
        output_type=output_type,
        model_settings=settings
    )
    
    # Wrap the agent's run method to add timing
    original_run = agent.run
    
    async def timed_run(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await original_run(*args, **kwargs)
            end_time = time.perf_counter()
            logger.info(f"Agent '{model}' call completed in {end_time - start_time:.3f}s")
            return result
        except Exception as e:
            end_time = time.perf_counter()
            logger.error(f"Agent '{model}' call failed after {end_time - start_time:.3f}s: {str(e)}")
            raise
    
    # Replace the run method with our timed version
    agent.run = timed_run
    
    return agent


import pytesseract
import numpy as np

async def scale_image_to_size(upload_file: bytes, target_size: Tuple[int, int] = (1000, 1000)) -> bytes:
    # Read the uploaded file
    image_data = io.BytesIO(upload_file)
    # Open the image using PIL
    img = Image.open(image_data)
    # Convert to RGB if necessary (for JPEG compatibility)
    if img.mode != 'RGB':
        # Handle different modes properly
        if img.mode in ('RGBA', 'LA', 'P'):
            # For RGBA/LA/P modes, create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                # Convert palette to RGBA first
                img = img.convert('RGBA')
            # Paste image onto background with alpha channel if present
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        else:
            # For grayscale and other modes, convert directly to RGB
            img = img.convert('RGB')
    # Calculate the scale factor to fit within target size while preserving aspect ratio
    width, height = img.size
    target_width, target_height = target_size
    scale = min(target_width / width, target_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    # Resize the image using LANCZOS resampling
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    # Create a new image with the target size and paste the resized image centered
    result = Image.new('RGB', target_size, (255, 255, 255))
    result.paste(img, ((target_width - new_width) // 2, (target_height - new_height) // 2))
    # Save as JPEG with quality 90
    output = io.BytesIO()
    result.save(output, format='JPEG', quality=90, optimize=True)
    # Return the bytes
    return output.getvalue()


async def _extract_labels_from_image(binary_image: bytes) -> TextBoundingBoxContainer:
    """Extract text labels from an image using a labeler agent."""
    logger.info("Starting label extraction from image")
    
    # Store original dimensions for coordinate mapping
    original_image_data = io.BytesIO(binary_image)
    original_img = Image.open(original_image_data)
    logger.info("Image opened")
    original_width, original_height = original_img.size
    
    # Calculate coordinate mapping
    canvas_width, canvas_height = 1000, 1000
    scale = min(canvas_width / original_width, canvas_height / original_height)
    scaled_width = int(original_width * scale)
    scaled_height = int(original_height * scale)
    offset_x = (canvas_width - scaled_width) // 2
    offset_y = (canvas_height - scaled_height) // 2
    
    mapping = CoordinateMapping(
        original_width=original_width,
        original_height=original_height,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        scale_x=scale,
        scale_y=scale,
        offset_x=offset_x,
        offset_y=offset_y
    )


    # Scale image for processing
    logger.info("Scaling image")
    scaled_image = await scale_image_to_size(binary_image)
    logger.info("Image scaled successfully")

    # Fallback to LLM-based approach
    labeler = build_chat_agent(
        f"https://llm.hnatekmar.dev/{IMAGE_MODEL}/v1",
        IMAGE_MODEL,
        LABEL_PROMPT,
        output_type=TextBoundingBoxContainer,
        settings=image_model_samplers,
    )
    # Extract labels
    labels = await labeler.run([
        BinaryContent(
            data=scaled_image,
            media_type="image/jpeg"
        )
    ])
    
    logger.info(f"Labels extracted: {len(labels.output.labels)} labels found")
    
    # Transform coordinates to original scale
    transformed_labels = []
    for label in labels.output.labels:
        original_bbox = transform_coordinates_to_original(label.bbox_2d, mapping)
        transformed_labels.append(TextBoundingBox(
            bbox_2d=original_bbox,
            text=label.text
        ))
    
    return TextBoundingBoxContainer(labels=transformed_labels)


x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3

async def _extract_text_from_labels(
    response_labels: List[TextBoundingBox],
) -> List[Label]:
    """Extract text from each labeled region using OCR."""
    logger.info("Starting OCR text extraction")

    labels = []
    for label in response_labels:
        labels.append(
            Label(
                text=label.text,  # Will be filled by OCR
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
    return labels

async def _translate_labels(
    labels: List[Label],
    translate_language: str
) -> List[Label]:
    """Translate text in labels to the specified language."""
    logger.info(f"Translation requested to {translate_language}")
    TRANSLATE_PROMPT_TEMPLATE = f"""
    You are a professional translator specializing in accurate and natural translations.

    **Task:** Translate the given text into {translate_language}.

    **Requirements:**
    - Provide ONLY the translated text without any explanations or additional commentary
    - Preserve the original meaning, tone, and intent
    - Ensure the translation sounds natural and fluent to native speakers
    - Maintain any formatting, punctuation, or special characters where appropriate
    - If the text is already in {translate_language}, return it exactly as provided
    - For proper nouns (names, places, brands), use standard transliterations if applicable

    **Input:** Text to be translated
    **Output:** Translated text only
    """
    translate_prompt = TRANSLATE_PROMPT_TEMPLATE.format(language=translate_language)
    translator = build_chat_agent(
        f"https://llm.hnatekmar.dev/{TRANSLATION_MODEL}/v1",
        TRANSLATION_MODEL,
        translate_prompt,
        settings=translation_model_samplers,
        output_type=str
    )
    logger.info("Translator agent built successfully")

    # Create translation tasks
    translation_tasks = [
        translator.run(label.text) for label in labels
    ]
    logger.info(f"Created {len(translation_tasks)} translation tasks")

    # Execute all translations concurrently
    translated_results = await asyncio.gather(*translation_tasks)
    logger.info("All translation tasks completed")

    # Update labels with translated text
    for label, result in zip(labels, translated_results):
        label.text = result.output.lstrip()
    logger.info("Translated results added to labels")
    return labels


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

    # Step 1: Extract labels from the image
    step1_start = time.perf_counter()
    binary_image = await data.read()
    
    # Extract original info for coordinate mapping
    original_image_data = io.BytesIO(binary_image)
    original_img = Image.open(original_image_data)
    
    response_labels = await _extract_labels_from_image(binary_image)
    labels = await _extract_text_from_labels(response_labels.labels)
    
    # Create response with coordinate mapping
    coordinate_mapping = CoordinateMapping(
        original_width=original_img.width,
        original_height=original_img.height,
        canvas_width=1000,
        canvas_height=1000,
        scale_x=min(1000 / original_img.width, 1000 / original_img.height),
        scale_y=min(1000 / original_img.width, 1000 / original_img.height),
        offset_x=(1000 - int(original_img.width * min(1000 / original_img.width, 1000 / original_img.height))) // 2,
        offset_y=(1000 - int(original_img.height * min(1000 / original_img.width, 1000 / original_img.height))) // 2
    )
    
    response = AnnotationResponse(
        labels=labels,
        coordinate_mapping=coordinate_mapping
    )
    
    # Step 2: Handle translation if requested
    if translate:
        translate_start = time.perf_counter()
        response.labels = await _translate_labels(response.labels, translate_language)
        translate_end = time.perf_counter()
        logger.info(f"Step 2 (translation) took {translate_end - translate_start:.3f}s")
    
    total_duration = time.perf_counter() - start_time
    logger.info(f"Image annotation process completed in {total_duration:.3f}s")
    return response