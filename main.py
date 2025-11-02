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

IMAGE_MODEL = "qwen3-8b-instruct"
TRANSLATION_MODEL = "qwen3-30b-instruct"
LABEL_PROMPT = """
You are a text region detection agent for machine translation workflows.

**Task:** Identify and localize all text regions in the input image.

**Input:** A single image containing text (e.g., speech bubbles, paragraphs, captions, signs, labels).

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

instruct_sampler = ModelSettings(
    temperature=0.7,
    extra_body={
        "top_p": 0.8,
        "top_k": 20,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
        "max_tokens": 32768
    }
)

thinking_sampler = ModelSettings(
    temperature=0.6,
    extra_body={
        "top_p": 0.95,
        "top_k": 20,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0,
        "max_tokens": 40960
    }
)

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


class LabelWithoutText(BaseModel):
    bbox_2d: List[float]  # [x1, y1, x2, y2] format
    text: str

class AnnotationResponse(BaseModel):
    labels: List[Label]

class AnnotateWithoutText(BaseModel):
    labels: List[LabelWithoutText]

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

async def _detect_languages_from_image(binary_image: bytes) -> List[str]:
    """Detect languages present in an image using LLM."""
    logger.info("Detecting languages in image")
    language_detector = build_chat_agent(
        f"https://llm.hnatekmar.dev/{IMAGE_MODEL}/v1",
        IMAGE_MODEL,
        f"""
        You are a language detection agent.
        - Your input is a single image
        - Identify and return the list of languages present in the image
        - Return only the list of language names, one per line
        - Languages that are available are {pytesseract.get_languages()}
        """,
        output_type=List[str],
        settings=instruct_sampler,
    )
    scaled_image = await scale_image_to_size(binary_image)
    languages = await language_detector.run([
        BinaryContent(
            data=scaled_image,
            media_type="image/jpeg"
        )
    ])
    logger.info(f"Detected languages: {languages.output}")
    return languages.output

async def _extract_labels_with_tesseract(binary_image: bytes) -> List[LabelWithoutText]:
    """Extract labels using Tesseract OCR with language-specific bounding boxes."""
    try:
        languages = await _detect_languages_from_image(binary_image)
        # Generate language string for pytesseract
        lang_string = '+'.join(languages)
        
        # Convert bytes to OpenCV image
        image_array = np.frombuffer(binary_image, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Apply preprocessing steps for better OCR results
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3,3), 0)
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Convert back to PIL Image for pytesseract
        pil_image = Image.fromarray(thresh)
        
        data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT, lang=lang_string)
        print(data)
        print(len(data['level']))
        labels = []
        for i in range(len(data['level'])):
            if data['level'][i] in [3]:  # confidence threshold
                labels.append(LabelWithoutText(
                    bbox_2d=[
                        (data['left'][i] / pil_image.width) * 1000,
                        (data['top'][i] / pil_image.height) * 1000,
                        ((data['left'][i] + data['width'][i]) / pil_image.width) * 1000,
                        ((data['top'][i] + data['height'][i]) / pil_image.height) * 1000
                    ]
                ))
        return []
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return []

async def _extract_labels_from_image(binary_image: bytes) -> AnnotateWithoutText:
    """Extract text labels from an image using a labeler agent."""
    logger.info("Starting label extraction from image")
    
    # Try using Tesseract first
    # try:
    #     tesseract_labels = await _extract_labels_with_tesseract(binary_image)
    #     if tesseract_labels:
    #         logger.info("Successfully extracted labels using Tesseract")
    #         return AnnotateWithoutText(labels=tesseract_labels)
    # except Exception as e:
    #     logger.warning(f"Tesseract extraction failed, falling back to LLM: {e}")

    # Fallback to LLM-based approach
    labeler = build_chat_agent(
        f"https://llm.hnatekmar.dev/{IMAGE_MODEL}/v1",
        IMAGE_MODEL,
        LABEL_PROMPT,
        output_type=AnnotateWithoutText,
        settings=instruct_sampler,
    )
    scaled_image = await scale_image_to_size(binary_image)

    logger.debug("Image scaled successfully")
    labels = await labeler.run([
        BinaryContent(
            data=scaled_image,
            media_type="image/jpeg"
        )
    ])
    logger.debug(f"Labels extracted: {len(labels.output.labels)} labels found")
    return labels.output

x1_i = 0
y1_i = 1
x2_i = 2
y2_i = 3

async def _extract_text_from_labels(
    response_labels: List[LabelWithoutText],
    original_img: Image.Image,
    ocr_agent: Agent
) -> List[Label]:
    """Extract text from each labeled region using OCR."""
    logger.info("Starting OCR text extraction")
    ocr_tasks = []
    valid_labels = response_labels
    # valid_labels = [
    #     label for label in response_labels
    #     if (label.bbox_2d[x2_i] - label.bbox_2d[x1_i]) > 16 and (label.bbox_2d[y2_i] - label.bbox_2d[y1_i]) > 32
    # ]
    # for label in valid_labels:
    #     # Crop the region from the original image
    #     top = max(0, int((label.bbox_2d[y1_i] / 1000.0) * original_img.height))
    #     left = max(0, int((label.bbox_2d[x1_i] / 1000.0) * original_img.width))
    #     right = min(original_img.width,int((label.bbox_2d[x2_i] / 1000.0) * original_img.width))
    #     bottom = min(original_img.height,  int((label.bbox_2d[y2_i] / 1000.0) * original_img.height))
    #     # Crop the region
    #     cropped_img = original_img.crop((left, top, right, bottom))
    #     # Convert cropped image to bytes
    #     img_bytes = io.BytesIO()
    #     cropped_img.save(img_bytes, format='JPEG', quality=90)
    #     img_bytes.seek(0)
    #     scaled_down_ocr_image = await scale_image_to_size(img_bytes.getvalue())
    #     # Run OCR on the cropped region
    #     ocr_task = ocr_agent.run([
    #         BinaryContent(
    #             data=scaled_down_ocr_image,
    #             media_type="image/jpeg"
    #         )
    #     ])
    #     ocr_tasks.append(ocr_task)
    # logger.info(f"Created {len(ocr_tasks)} OCR tasks")
    # # Execute all OCR tasks concurrently
    # ocr_results = await asyncio.gather(*ocr_tasks)
    # logger.debug("All OCR tasks completed")
    # Update labels with OCR results
    labels = []
    for label in valid_labels:
        labels.append(
            Label(
                text=label.text,
                y1=label.bbox_2d[y1_i],
                x1=label.bbox_2d[x1_i],
                y2=label.bbox_2d[y2_i],
                x2=label.bbox_2d[x2_i],
            )
        )
        print(labels[-1])
    logger.debug("OCR results added to labels")
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
        settings=instruct_sampler,
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
    
    # Step 1: Extract labels from the image
    binary_image = await data.read()
    response_labels = await _extract_labels_from_image(binary_image)
    
    # Step 2: Extract text from each label region using OCR
    original_image_data = io.BytesIO(binary_image)
    original_img = Image.open(original_image_data)
    
    # Create OCR agent for text extraction
    OCR_PROMPT = """
    You are an OCR agent that extracts text from a specific region of an image.
    - You are given cropped image 
    - Return only the text that you can see
    """
    ocr_agent = build_chat_agent(
        f"https://llm.hnatekmar.dev/{IMAGE_MODEL}/v1",
        IMAGE_MODEL,
        OCR_PROMPT,
        output_type=str,
        settings=instruct_sampler
    )
    logger.debug("OCR agent built successfully")
    
    labels = await _extract_text_from_labels(response_labels.labels, original_img, ocr_agent)
    response = AnnotationResponse(
        labels=labels
    )
    
    # Step 3: Handle translation if requested
    if translate:
        response.labels = await _translate_labels(response.labels, translate_language)
        
    logger.info("Image annotation process completed successfully")
    return response